from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)


def get_publicpb_keyboard(pb_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data=f"publicpb:{pb_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"nopublic:{pb_id}")
        ]
    ])


def get_opinion_keyboard(opinion_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data=f"opinion_confirm:{opinion_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"opinion_cancel:{opinion_id}")
        ]
    ])



main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Мнение', callback_data='mnenie'),
                                             InlineKeyboardButton(text='ПБ', callback_data='PB')]
                                             ])


formatselect = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Формат Пруфбаттла',
                                                                           callback_data='pb_format')],
                                                     [InlineKeyboardButton(text='Формат Голосового чата',
                                                                           callback_data='gch')],
                                                     [InlineKeyboardButton(text='Формат Дискуссии',
                                                                           callback_data='discussion_format')]
                                                     ])


pbformat = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Формат "Тактика"',
                                                                           callback_data='classic_f')],
                                                     [InlineKeyboardButton(text='Формат "Ходы"',
                                                                           callback_data='hodi_f')]
                                                     ])


public = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅", callback_data="yes"),
                                                InlineKeyboardButton(text="❌", callback_data="no")]
                                                    ])


accept = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅", callback_data="right"),
                                                InlineKeyboardButton(text="❌", callback_data="wrong")]
                                                    ])

opinion_type_select = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Одиночное", callback_data="single"),
            InlineKeyboardButton(text="Одиночное", callback_data="single") # Временная мера, не работают групповые пока
        ]
    ]
)


moderate_opinion = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data="approve"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
        ]
    ]
)