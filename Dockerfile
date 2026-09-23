FROM eclipse-temurin:21-jdk-jammy AS build

WORKDIR /workspace
COPY .mvn .mvn
COPY mvnw pom.xml ./
RUN ./mvnw -B -DskipTests dependency:go-offline
COPY src src
RUN ./mvnw -B -DskipTests package

FROM eclipse-temurin:21-jre-jammy

RUN apt-get update \
    && apt-get install --no-install-recommends -y python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN python3 -m venv /opt/ufc-venv \
    && /opt/ufc-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/ufc-venv/bin/pip install --no-cache-dir -r requirements.txt

COPY --from=build /workspace/target/ufc-prediction-1.0.0-SNAPSHOT.jar app.jar
COPY regression.py ufc_predictor.py ufcstats_client.py ./
COPY stats_processed.csv raw_fighter_details.csv ./

ENV PYTHON_EXECUTABLE=/opt/ufc-venv/bin/python3 \
    UFC_PROJECT_ROOT=/app \
    JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=35.0 -XX:InitialRAMPercentage=10.0"

EXPOSE 10000
ENTRYPOINT ["java", "-jar", "app.jar"]
