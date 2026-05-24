FROM ghcr.io/userver-framework/ubuntu-22.04-userver-pg-dev:latest

WORKDIR /app

COPY . .

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j$(nproc)

EXPOSE 8080

CMD ["./build/delivery_service", \
     "--config", "configs/static_config.yaml", \
     "--config_vars", "configs/config_vars.yaml"]
