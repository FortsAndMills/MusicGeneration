## Глобальная задача

[Подходы к генерации музыки](https://github.com/FortsAndMills/MusicGeneration/tree/master/%D0%9F%D0%BE%D0%B4%D1%85%D0%BE%D0%B4%D1%8B%20%D0%BA%20%D0%B3%D0%B5%D0%BD%D0%B5%D1%80%D0%B0%D1%86%D0%B8%D0%B8%20%D0%BC%D1%83%D0%B7%D1%8B%D0%BA%D0%B8) - сборник ссылочек по этой теме. Нас конкретнее интересует именно генерация midi-файла. Глобально подходов два: просто что-нибудь придумать, основываясь на муз. теории, или запихнуть много данных в нейросеть.

## Работа с midi в питоне
Существует много библиотек под питон, я использую [mido](https://mido.readthedocs.io/en/latest/).

Во всех экспериментах используется songs.py - простенький модуль, который пока может:
* загружать миди-файлы
* проверять их на то, что они не выходят за диапазон
* проигрывать их прямо в ноутбуке
* переводить в булев массив [время x количество клавиш], пока без квантизации
* создавать новый миди-файл по передаваемым строкам булева массива

## Данные

На коленке было записано [34 песенки](https://github.com/FortsAndMills/MusicGeneration/tree/master/basic%20midi) из сборника произведений для первоклашек. Первая дорожка - кузнечик, с которого обычно и начинают.
* три из них выходят за диапазон в 13 клавиш; ещё несколько выходят за диапазон, но модуль songs транспонированием автоматически это исправляет
* если стартовать с инициализации памяти первым тактом, то будут "пересечения" - первый такт у нескольких мелодий совпадает.
* ещё есть песенка whomadethis.mid, которая как-то не очень похожа на музыку, но какой-то человек её умудрился написать. Предлагается оставить для валидации))

# Упрощённая задача

Пока возьмём только 13 клавиш (одна октава + верхняя до, в стандартных обозначениях - C, C#, D, D#, E, F, F#, G, G#, A, A#, B и ещё одна C). В каждый момент времени клавиша либо нажимается, либо отпущена (т.е. понятия зажатой клавиши нет).

Также пока предположим отсутствие реккурентности; вместо памяти будем подавать на вход не только текущий, но и предыдущие моменты времени (скажем, 4 такта; вроде оптимально, кстати, будет брать 1, 2, 4, 8 и т.д. до некоторого предела).

## Переобучение vs запоминание

Первоначальная идея была реализовать обучение с подкреплением (нейросеть на кучи данных, выдающая reward ("слушатель") + "исполнитель", обучающийся на этом reward-е через Q-обучение или нейроэволюцию). Сильно упростим эту задачу: хотим всего лишь научить исполнителя играть кузнечика.

- если алгоритм детерминирован, то на входе, совпадающий с началом выученной песенки, он в точности повторит её без вероятности придумать другое продолжение. Есть способы обойти это - дополнительный вход, равный 1 при изучении песни, который при желании "импровизировать" выключается.
- а вот на новом входе алгоритм теоретически может выдать что-то ещё. Если запоминание обучающей выборки происходит каким-то образом с выделением закономерностей и знаний, то так может и что-то получится на выходе.
- в конце концов, если мы не можем решить эту задачу для "исполнителя" ("нажми вот эти кнопки в заданной последовательности и никак иначе"), то что уж говорить о задаче "а ну, играй на 13 кнопках то, что слушатель посчитает музыкой".

# NEAT

[Нейроэволюционный подход](https://github.com/FortsAndMills/MusicGeneration/tree/master/%D0%9D%D0%B5%D0%B9%D1%80%D0%BE%D1%8D%D0%B2%D0%BE%D0%BB%D1%8E%D1%86%D0%B8%D1%8F) хорош тем, что якобы умеет учиться нажимать кнопки (в данном случае - клавиши) в правильной последовательности. Однако пока что заставить его построить нейросеть, которая запомнит даже первые несколько тактов, [не удалось](https://github.com/FortsAndMills/MusicGeneration/tree/master/%D0%9D%D0%B5%D0%B9%D1%80%D0%BE%D1%8D%D0%B2%D0%BE%D0%BB%D1%8E%D1%86%D0%B8%D1%8F#ЭКСПЕРИМЕНТЫ) :( Возможно, я криворукий. 

Поэтому исследование ВНЕЗАПНО приняло неожиданный оборот:

# Булевоалгебраический подход

Лаконичная интерпретация идеи от А.Думбая (2017):

![alt text](https://github.com/FortsAndMills/MusicGeneration/blob/master/Discon/Opinion.gif)
