FROM python:3.11-slim

WORKDIR /app

# Добавляем PYTHONPATH для корректного поиска модуля shared
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir --upgrade pip

COPY services/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip show pymongo | grep Version | grep 4.13.2 || exit 1
RUN pip show redis | grep Version | grep 5.0.8 || exit 1

COPY proto/ /app/proto/
COPY shared/ /app/shared/
# Добавляем отладку для проверки содержимого /app/shared
RUN ls -R /app/shared || dir /app/shared

COPY services/auth-service/ /app/

RUN python -m grpc_tools.protoc -I./proto --python_out=./app/infrastructure/adapters/inbound/grpc --grpc_python_out=./app/infrastructure/adapters/inbound/grpc ./proto/auth.proto
RUN python -m grpc_tools.protoc -I./proto --python_out=./app/infrastructure/adapters/outbound/grpc --grpc_python_out=./app/infrastructure/adapters/outbound/grpc ./proto/user.proto

RUN sed -i 's/import auth_pb2 as auth__pb2/from . import auth_pb2 as auth__pb2/' ./app/infrastructure/adapters/inbound/grpc/auth_pb2_grpc.py
RUN sed -i 's/import user_pb2 as user__pb2/from . import user_pb2 as user__pb2/' ./app/infrastructure/adapters/outbound/grpc/user_pb2_grpc.py

CMD ["python", "app/main.py"]