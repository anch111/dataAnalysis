from gigachat import GigaChat
from gigachat.models import Chat, Function, FunctionParameters, Messages, MessagesRole

import json
from ddgs import DDGS

token = 'MDE5YWJhYjctNDE1ZS03YmQ4LWI5Y2EtMGU1NDg5MjJjMGM2OmYyZDk0YTkzLTA4NzItNGI1YS04YTk3LWYyNjc4NmU4ZTVkZQ=='
MESSAGE = "погода в чебоксарах"
with GigaChat(credentials=token, verify_ssl_certs=False) as giga:
    response = giga.chat(MESSAGE)

#print(response.choices[0].message.content)

from IPython.display import display, Markdown

messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content=(
                "Ты писатель Достоевский\n"
                "## Инструкция\n"
                "Ответ должен подходить студенту начальных курсов бакалавриата, изучающему технологии искусственного интеллекта\n"
                "## Формат ответа\n"
                "Текст и таблицы в формате markdown\n"
            )
        ),
        Messages(
            role=MessagesRole.USER,
            content=MESSAGE
        ),
    ]

with GigaChat(credentials=token, verify_ssl_certs=False) as giga:
    response = giga.chat(MESSAGE)
    content = response.choices[0].message.content
    # display(Markdown("<blockquote>\n\n"+content))

payload = Chat(
    messages=messages,
    temperature=0.7,
    max_tokens=100,
)

model = GigaChat(
    model="GigaChat-2-Pro",
    credentials=token,
    verify_ssl_certs=False
)


response = model.chat(payload)

# print(response.choices[0].message.content)

def search_ddg(search_query):
    """Поиск в DuckDuckGo.
        Полезен, когда нужно ответить на вопросы о текущих событиях.
        Входными данными должен быть поисковый запрос."""
    return DDGS().text(search_query, max_results=10)

results = search_ddg(MESSAGE)
# print(results[1])

search_func = Function(
    name="duckduckgo_search",
    description="Используй ТОЛЬКО для вопросов о погоде.",
    parameters=FunctionParameters(
        type="object",
        properties={"query": {"type": "string"}},
        required=["query"],
    ),
)

messages = [
        Messages(role=MessagesRole.USER, content=MESSAGE)
    ]
chat = Chat(messages=messages, functions=[search_func])
resp = model.chat(chat).choices[0]
message = resp.message
print(resp.finish_reason)

# Если модель хочет вызвать функцию
if resp.finish_reason == "function_call":
    func_name = message.function_call.name
    query = message.function_call.arguments["query"]

    # Выполняем функцию
    result = search_ddg(query)

    # Шаг 2: отправляем результат обратно модели
    messages.extend([
        message,  # сообщение с function_call
        Messages(role=MessagesRole.FUNCTION, content=json.dumps({"result": result}, ensure_ascii=False))
    ])
    final_resp = model.chat(Chat(messages=messages)).choices[0]
    response = final_resp.message.content
else:
    # Модель ответила сразу
    print('МОДЕЛЬ ОТВЕТИЛА СРАЗУ')
    response = message.content

# print(response)

import re


def safe_calculate(expression: str) -> str:
    """
    Выполняет математическое выражение.
    Поддерживает: +, -, *, /, **, скобки, числа с точкой.
    Безопасен: разрешает ТОЛЬКО математические символы.
    """
    # Разрешённые символы: цифры, операторы, скобки, точка, пробелы
    if not re.fullmatch(r'[\d+\-*/().\s]+', expression):
        return "Ошибка: выражение содержит недопустимые символы."

    try:
        # Ограничиваем сложность (например, не даём выполнить 9**9**9)
        if '^' in expression or len(expression) > 50:
            return "Ошибка: выражение слишком сложное или длинное."

        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Ошибка вычисления: {str(e)}"

# print(safe_calculate('3*(4+5)**2'))

calculate_func = Function(
    name="calculate",
    description="Выполняет математические вычисления. Передавай ТОЛЬКО выражение в виде строки, например: '2 + 3 * 4'.",
    parameters=FunctionParameters(
        type="object",
        properties={
            "expression": {
                "type": "string",
                "description": "Математическое выражение (только цифры, +, -, *, /, **, скобки)"
            }
        },
        required=["expression"],
    ),
)

message = 'Сколько будет cos(90)'

messages = [
    Messages(role=MessagesRole.USER, content=message)
]

chat = Chat(messages=messages, functions=[calculate_func])

resp = model.chat(chat).choices[0]
message = resp.message

if resp.finish_reason == "function_call":
    func = message.function_call
    if func.name == "calculate":
        expr = func.arguments.get("expression", "")
        result = safe_calculate(expr)
        # Возвращаем результат модели
        messages.extend([
            message,
            Messages(role=MessagesRole.FUNCTION, content=result)
        ])
        # Получаем финальный ответ
        final = model.chat(Chat(messages=messages)).choices[0]
        response =  final.message.content
else:
    # Модель ответила без вычислений (например, объяснила задачу)
    response = message.content

print(response)
