#include "AXP2101.h"

#define AXP2101_ADDR 0x34

// Registradores principais
#define REG_CHIP_ID     0x03
#define REG_BAT_V_H     0x78
#define REG_BAT_V_L     0x79
#define REG_BAT_I_H     0x7A
#define REG_BAT_I_L     0x7B
#define REG_CHG_STATUS  0x01

// LDO / DCDC enable register
#define REG_POWER_OUT   0x69

AXP2101::AXP2101() {
    wire = nullptr;
    i2c_addr = AXP2101_ADDR;
}

bool AXP2101::begin(TwoWire *w, uint8_t addr) {
    wire = w;
    i2c_addr = addr;

    wire->beginTransmission(i2c_addr);
    if (wire->endTransmission() != 0) {
        return false;  // Não encontrou
    }

    uint8_t id = read8(REG_CHIP_ID);
    if (id == 0x00 || id == 0xFF) {
        return false;
    }

    return true;
}

uint8_t AXP2101::read8(uint8_t reg) {
    wire->beginTransmission(i2c_addr);
    wire->write(reg);
    wire->endTransmission(false);

    wire->requestFrom(i2c_addr, (uint8_t)1);
    return wire->read();
}

uint16_t AXP2101::read12(uint8_t regH, uint8_t regL) {
    uint8_t h = read8(regH);
    uint8_t l = read8(regL);
    return ((uint16_t)h << 4) | (l & 0x0F);
}

void AXP2101::write8(uint8_t reg, uint8_t val) {
    wire->beginTransmission(i2c_addr);
    wire->write(reg);
    wire->write(val);
    wire->endTransmission();
}

// ----------- Controle de Saídas -----------

bool AXP2101::enableLDO2(bool en) {
    uint8_t v = read8(REG_POWER_OUT);
    if (en) v |= 0x02;
    else    v &= ~0x02;
    write8(REG_POWER_OUT, v);
    return true;
}

bool AXP2101::enableLDO3(bool en) {
    uint8_t v = read8(REG_POWER_OUT);
    if (en) v |= 0x04;
    else    v &= ~0x04;
    write8(REG_POWER_OUT, v);
    return true;
}

bool AXP2101::enableDCDC1(bool en) {
    uint8_t v = read8(REG_POWER_OUT);
    if (en) v |= 0x10;
    else    v &= ~0x10;
    write8(REG_POWER_OUT, v);
    return true;
}

bool AXP2101::enableDCDC2(bool en) {
    uint8_t v = read8(REG_POWER_OUT);
    if (en) v |= 0x20;
    else    v &= ~0x20;
    write8(REG_POWER_OUT, v);
    return true;
}

bool AXP2101::enableDCDC3(bool en) {
    uint8_t v = read8(REG_POWER_OUT);
    if (en) v |= 0x40;
    else    v &= ~0x40;
    write8(REG_POWER_OUT, v);
    return true;
}

// ----------- Medições -----------

float AXP2101::getBatteryVoltage() {
    uint16_t val = read12(REG_BAT_V_H, REG_BAT_V_L);
    return val * 1.1f;  // Conversão típica AXP2101
}

float AXP2101::getBatteryCurrent() {
    uint16_t val = read12(REG_BAT_I_H, REG_BAT_I_L);
    return val * 0.5f;  
}

bool AXP2101::isCharging() {
    uint8_t st = read8(REG_CHG_STATUS);
    return (st & 0x04) != 0;
}
