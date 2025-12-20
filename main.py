import asyncio
import time
import random
import os

from telethon import TelegramClient, errors
from telethon.errors import FloodWaitError

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    USE_TK = True
except ImportError:
    USE_TK = False

# ---------------  ВСТАВЬТЕ ВАШИ ДАННЫЕ ЗДЕСЬ ---------------
API_ID = 22937843  # Замените на ваш API ID
API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"  # Замените на ваш API Hash
# -----------------------------------------------------------

# Отправляем по 20 сообщений за батч, после чего ожидаем 48 часов
MESSAGES_PER_BATCH = 18
PROGRESS_FILE = "progress.txt"


async def authenticate_telegram():
    client = TelegramClient('session_name', API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.start()
        print("Успешная аутентификация!")
    except errors.PhoneNumberInvalidError:
        print("Ошибка: Неверный номер телефона.")
        exit(1)
    except errors.SessionPasswordNeededError:
        print("Ошибка: Требуется пароль двухфакторной аутентификации.")
        exit(1)
    except Exception as e:
        print("Ошибка подключения к Telegram:", e)
        exit(1)
    return client

async def ensure_client_connected(client):
    if not client.is_connected():
        await client.connect()
        if not await client.is_user_authorized():
            await client.start()


async def get_group_members(client, group_identifier):
    try:
        participants = await client.get_participants(group_identifier)
        users = []
        for user in participants:
            user_info = {
                'id': user.id,
                'username': user.username if user.username else None,
                'first_name': user.first_name,
                'last_name': user.last_name if user.last_name else None,
                'sent': False
            }
            users.append(user_info)
        return users
    except errors.ChatAdminRequiredError:
        print("Ошибка: У вас нет прав администратора в этой группе.")
        return []
    except ValueError:
        print("Ошибка: Неверный идентификатор группы.")
        return []
    except Exception as e:
        print("Ошибка получения участников группы:", e)
        return []


async def send_message(client, user, message_text, delay_min=15, delay_max=45):
    """Отправка сообщения с рандомной задержкой для минимизации риска блокировки."""
    try:
        await client.send_message(user['id'], message_text, parse_mode="HTML")
        print(f"Сообщение отправлено пользователю {user.get('first_name', 'Неизвестно')} (ID: {user['id']})")
        # Рандомная задержка между сообщениями
        await asyncio.sleep(random.randint(delay_min, delay_max))
        return True
    except FloodWaitError as e:
        print(f"Достигнут лимит запросов. Ожидание {e.seconds} секунд...")
        await asyncio.sleep(e.seconds + random.randint(5, 10))
        return False
    except errors.PeerFloodError:
        print("Слишком много запросов. Попробуйте позже.")
        await asyncio.sleep(60)
        return False
    except errors.UserPrivacyRestrictedError:
        print(f"Не удалось отправить сообщение пользователю {user['id']}: настройки приватности.")
        return True  # Считаем, что сообщение "отправлено", чтобы не повторять попытку
    except Exception as e:
        print(f"Ошибка отправки сообщения пользователю {user['id']}: {e}")
        return False


def load_progress(members):
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                sent_ids = [int(line.strip()) for line in f]
                for user in members:
                    if user['id'] in sent_ids:
                        user['sent'] = True
        except Exception as e:
            print(f"Ошибка загрузки прогресса: {e}")


def save_progress(members):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            for user in members:
                if user['sent']:
                    f.write(str(user['id']) + "\n")
    except Exception as e:
        print(f"Ошибка сохранения прогресса: {e}")


async def main():
    client = await authenticate_telegram()

    if USE_TK:
        root = tk.Tk()
        root.withdraw()
        group_input = simpledialog.askstring("Группа", "Введите имя, ID или ссылку на группу:")
        if group_input is None or group_input.strip() == "":
            print("Группа не указана. Завершение работы.")
            await client.disconnect()
            return

        message_filepath = filedialog.askopenfilename(
            title="Выберите файл с сообщением",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        root.destroy()
        if not message_filepath:
            print("Файл с сообщением не выбран. Завершение работы.")
            await client.disconnect()
            return
        try:
            with open(message_filepath, "r", encoding="utf-8") as f:
                message_text = f.read()
        except FileNotFoundError:
            print("Файл с сообщением не найден.")
            await client.disconnect()
            return
        except Exception as e:
            print(f"Ошибка чтения файла с сообщением: {e}")
            await client.disconnect()
            return
    else:
        group_input = input("Введите имя, ID или ссылку на группу: ")
        if not group_input.strip():
            print("Группа не указана. Завершение работы.")
            await client.disconnect()
            return
        message_filepath = input("Введите путь к файлу с сообщением: ")
        try:
            with open(message_filepath, "r", encoding="utf-8") as f:
                message_text = f.read()
        except FileNotFoundError:
            print("Файл не найден.")
            await client.disconnect()
            return
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            await client.disconnect()
            return

    members = await get_group_members(client, group_input)
    if not members:
        await client.disconnect()
        return

    load_progress(members)
    unsent_members = [user for user in members if not user['sent']]
    print(f"Всего участников: {len(members)}, отправлено: {len(members) - len(unsent_members)}, осталось: {len(unsent_members)}")

    while unsent_members:
        batch_count = 0
        for user in unsent_members:
            if batch_count >= MESSAGES_PER_BATCH:
                break
            success = await send_message(client, user, message_text)
            if success:
                user['sent'] = True
                batch_count += 1
                save_progress(members)
        unsent_members = [user for user in members if not user['sent']]
        if unsent_members:
            print(f"Отправлено {MESSAGES_PER_BATCH} сообщений. Ожидание 22 часов перед следующей отправкой...")
            await client.disconnect()
            await asyncio.sleep(72000)
            client = await authenticate_telegram()
        else:
            break
    
    print("Рассылка завершена. Все участники получили сообщение.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

