ARG OTP_VERSION=2.7.0
ARG GTFS_URL=https://mkuran.pl/gtfs/warsaw.zip

FROM eclipse-temurin:21-jdk AS builder
WORKDIR /opt/otp

RUN apt-get update \
 && apt-get install -y --no-install-recommends unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ARG OTP_VERSION
RUN curl -fsSL -o otp.jar \
    "https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/${OTP_VERSION}/otp-shaded-${OTP_VERSION}.jar"

COPY warsaw.pbf .

ARG GTFS_URL
RUN curl -fsSL -o gtfs.zip "${GTFS_URL}" \
 && unzip -q gtfs.zip -d gtfs \
 && rm gtfs.zip

RUN java -Xmx6G -jar otp.jar --build --save .

FROM eclipse-temurin:21-jre
WORKDIR /opt/otp

COPY --from=builder /opt/otp/otp.jar   .
COPY --from=builder /opt/otp/graph.obj .

EXPOSE 8080
ENTRYPOINT ["java", "-Xmx2G", "-jar", "otp.jar", "--load", "/opt/otp"]

