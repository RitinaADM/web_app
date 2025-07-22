FROM python:3.11-slim

WORKDIR /app

# Обновляем pip для избежания проблем с установкой
RUN pip install --no-cache-dir --upgrade pip

COPY services/user-service/requirements.txt .
# Устанавливаем зависимости без кэша
RUN pip install --no-cache-dir -r requirements.txt
# Проверяем, что pymongo версии 4.13.2 установлен
RUN pip show pymongo | grep Version | grep 4.13.2 || exit 1
RUN pip show redis | grep Version | grep 5.0.8 || exit 1

# Копируем proto файл и исходный код
COPY proto/ /app/proto/
COPY services/user-service/ /app/

# Генерируем протофайлы
RUN python -m grpc_tools.protoc -I./proto --python_out=./app/infrastructure/adapters/inbound/grpc --grpc_python_out=./app/infrastructure/adapters/inbound/grpc ./proto/user.proto

# Исправляем импорт в user_pb2_grpc.py
RUN sed -i 's/import user_pb2 as user__pb2/from . import user_pb2 as user__pb2/' ./app/infrastructure/adapters/inbound/grpc/user_pb2_grpc.py

CMD ["python", "app/main.py"]