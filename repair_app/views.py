from django.shortcuts import render


# Create your views here.

# Представление главной страницы сайта.
# Отображает приветственное сообщение и название сайта RepAir.
def index(request):
    context = {
        'title': 'RepAir - Главная',
        'content': 'Сервис ремонта RepAir - Вдохните новую жизнь в ваши средства передвижения!',
    }
    return render(request, 'repair_app/index.html', context);


def about(request):
    context = {
        'title': 'О нас',
        'content': 'О сервисе ремонта RepAir',
        'text_on_page': """""",
    }
    return render(request, 'repair_app/about.html', context);


def contacts(request):
    context = {
        'title': 'Контакты',
    }
    return render(request, 'repair_app/contacts.html', context);


def zakaz_and_dostavka(request):
    context = {
        'title': 'Заказ и оплата',
    }
    return render(request, 'repair_app/zakaz_and_dostavka.html', context);
