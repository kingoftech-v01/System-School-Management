from modeltranslation.translator import register, TranslationOptions
from .models import Room, TimeSlot


@register(Room)
class RoomTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(TimeSlot)
class TimeSlotTranslationOptions(TranslationOptions):
    fields = ('name',)
