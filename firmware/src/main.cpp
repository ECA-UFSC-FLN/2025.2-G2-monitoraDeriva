#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <LoRa.h>
#include <TinyGPSPlus.h>
#include "AXP2101.h"

// -------- T-Beam V2.1 GPIOs --------
#define LORA_SCK  5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_CS   18
#define LORA_RST  23
#define LORA_IRQ  26

// GPS
#define GPS_RX 34
#define GPS_TX 12
HardwareSerial GPS_Serial(1);

TinyGPSPlus gps;
AXP2101 power;

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("Iniciando T-Beam V2.1...");

    // ---------- PMU (AXP2101) ----------
    Wire.begin(21, 22);
    if (!power.begin(&Wire)) {
        Serial.println("Falha ao iniciar AXP2101!");
    } else {
        Serial.println("AXP2101 OK");
    }

    // ---------- GPS ----------
    GPS_Serial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);
    Serial.println("GPS OK");

    // ---------- LoRa ----------
    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);

    if (!LoRa.begin(915E6)) {
        Serial.println("Erro ao iniciar LoRa!");
        while (1);
    }
    Serial.println("LoRa OK");
}

unsigned long count = 0;

void loop() {

    // -------- GPS --------
    while (GPS_Serial.available()) {
        gps.encode(GPS_Serial.read());
    }

    if (gps.location.isUpdated()) {
        Serial.print("Lat: ");
        Serial.print(gps.location.lat(), 6);
        Serial.print("  Lon: ");
        Serial.println(gps.location.lng(), 6);
    }

    // -------- LoRa TX --------
    Serial.printf("Enviando pacote %lu\n", count);
    LoRa.beginPacket();
    LoRa.print("Pacote ");
    LoRa.print(count++);
    LoRa.endPacket();

    delay(1000);
}
