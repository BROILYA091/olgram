"""
Здесь работа с конкретным ботом
"""
from asyncio import sleep
from datetime import datetime
from aiogram import types
from aiogram.utils import exceptions
from aiogram import Bot as AioBot
from olgram.models.models import Bot
from olgram.utils.mix import send_stored_message
from server.server import unregister_token
from locales.locale import _


async def delete_bot(bot: Bot, call: types.CallbackQuery):
    """
    Пользователь решил удалить бота
    """
    try:
        await unregister_token(bot.decrypted_token())
    except exceptions.Unauthorized:
        # Вероятно пользователь сбросил токен или удалил бот, это уже не наши проблемы
        pass
    await bot.delete()
    await call.answer(_("Бот удалён"))
    try:
        await call.message.delete()
    except exceptions.TelegramAPIError:
        pass


async def reset_bot_text(bot: Bot, call: types.CallbackQuery):
    """
    Пользователь решил сбросить текст бота к default
    :param bot:
    :param call:
    :return:
    """
    bot.start_text = bot._meta.fields_map['start_text'].default
    await bot.save()
    await call.answer(_("Текст сброшен"))


async def reset_bot_second_text(bot: Bot, call: types.CallbackQuery):
    """
    Пользователь решил сбросить second text бота
    :param bot:
    :param call:
    :return:
    """
    bot.second_text = bot._meta.fields_map['second_text'].default
    await bot.save()
    await call.answer(_("Текст сброшен"))


async def select_chat(bot: Bot, call: types.CallbackQuery, chat: str):
    """
    Пользователь выбрал чат, в который хочет получать сообщения от бота
    :param bot:
    :param call:
    :param chat:
    :return:
    """
    if chat == "personal":
        bot.group_chat = None
        await bot.save()
        await call.answer(_("Выбран личный чат"))
        return
    if chat == "leave":
        bot.group_chat = None
        await bot.save()
        chats = await bot.group_chats.all()
        a_bot = AioBot(bot.decrypted_token())
        for chat in chats:
            try:
                await chat.delete()
                await a_bot.leave_chat(chat.chat_id)
            except exceptions.TelegramAPIError:
                pass
        await call.answer(_("Бот вышел из чатов"))
        await a_bot.session.close()
        return

    chat_obj = await bot.group_chats.filter(id=chat).first()
    if not chat_obj:
        await call.answer(_("Нельзя привязать бота к этому чату"))
        return
    bot.group_chat = chat_obj
    await bot.save()
    await call.answer(_("Выбран чат {0}").format(chat_obj.name))


async def threads(bot: Bot, call: types.CallbackQuery):
    bot.enable_threads = not bot.enable_threads
    await bot.save(update_fields=["enable_threads"])


async def additional_info(bot: Bot, call: types.CallbackQuery):
    bot.enable_additional_info = not bot.enable_additional_info
    await bot.save(update_fields=["enable_additional_info"])


async def olgram_text(bot: Bot, call: types.CallbackQuery):
    if await bot.is_promo():
        bot.enable_olgram_text = not bot.enable_olgram_text
        await bot.save(update_fields=["enable_olgram_text"])


async def antiflood(bot: Bot, call: types.CallbackQuery):
    bot.enable_antiflood = not bot.enable_antiflood
    await bot.save(update_fields=["enable_antiflood"])


async def mailing(bot: Bot, call: types.CallbackQuery):
    bot.enable_mailing = not bot.enable_mailing
    await bot.save(update_fields=["enable_mailing"])


async def go_mailing(bot: Bot, context) -> int:
    users = await bot.mailing_users
    a_bot = AioBot(bot.decrypted_token())

    count = 0

    print(f"start mailing {context}")

    for user in users:
        bot.last_mailing_at = datetime.now()
        await bot.save(update_fields=["last_mailing_at"])
        try:
            await sleep(0.05)
            try:
                await send_stored_message(context, a_bot, user.telegram_id)
            except exceptions.RetryAfter as err:
                await sleep(err.timeout)
                await send_stored_message(context, a_bot, user.telegram_id)
            count += 1
        except (exceptions.ChatNotFound, exceptions.BotBlocked, exceptions.UserDeactivated):
            await user.delete()
        except exceptions.TelegramAPIError:
            pass

    return count
