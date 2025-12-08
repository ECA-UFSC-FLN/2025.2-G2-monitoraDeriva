#pragma once
#include <Arduino.h>
#include <Wire.h>

class AXP2101 {
public:
    AXP2101();

    bool begin(TwoWire *w, uint8_t addr = 0x34);

    // Controle simples de tensões
    bool enableLDO2(bool en);
    bool enableLDO3(bool en);
    bool enableDCDC1(bool en);
    bool enableDCDC2(bool en);
    bool enableDCDC3(bool en);

    float getBatteryVoltage();
    float getBatteryCurrent();

    bool isCharging();

private:
    TwoWire *wire;
    uint8_t i2c_addr;

    uint8_t read8(uint8_t reg);
    uint16_t read12(uint8_t regH, uint8_t regL);
    void write8(uint8_t reg, uint8_t val);
};
