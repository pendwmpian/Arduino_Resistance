#include <Arduino.h>
#include <Wire.h>

#define SEND_ERROR_TO_SERIAL Serial.println("Failed to connect with device.")
#define SLAVE_ADDR 0x48

union Data {
    struct __attribute__((__packed__)) {
        uint32_t time;
        int16_t volt;
        uint8_t chk_sum = 0;
    };
    uint8_t bin[7];
};

void encodeCOBS(Data* dat, uint8_t* encoded){
    dat->chk_sum = 0;
    for(uint8_t i = 0; i < sizeof(Data) - 1; i++){
        dat->chk_sum += dat->bin[i];
    }
    encoded[sizeof(Data) + 1] = 0;
    uint8_t zero = 1;
    for(int8_t i = sizeof(Data) - 1; i >= 0; i--){
        if(dat->bin[i] != 0) encoded[i + 1] = dat->bin[i];
        else {encoded[i + 1] = zero; zero = 0;}
        zero++;
    }
    encoded[0] = zero;
}



void setup(void)
{
    Serial.begin(115200);

    Wire.begin();
    Wire.beginTransmission(SLAVE_ADDR);
    Wire.write(0x01);
    Wire.write(0x40);
    Wire.write(0xE3);
    if(Wire.endTransmission()) SEND_ERROR_TO_SERIAL;
}


void loop(void)
{
    Data result;
    uint8_t encoded[sizeof(Data) + 2];

    uint8_t conversion_ready = 0x00;
    while(conversion_ready & 0x80 != 0x00){
        Wire.beginTransmission(SLAVE_ADDR);
        Wire.write(0x01);
        Wire.endTransmission();
        Wire.requestFrom(SLAVE_ADDR, 2);
        while(Wire.available()){
            conversion_ready = Wire.read();
            Wire.read();
        }
    } 

    Wire.beginTransmission(SLAVE_ADDR);
    Wire.write(0x00);
    Wire.endTransmission();
    Wire.requestFrom(SLAVE_ADDR, 2);
    while(Wire.available()){
        result.volt = Wire.read() << 8;
        result.volt += Wire.read() & 0x00FF;
    }

    result.time = micros();
    encodeCOBS(&result, encoded);
    for(uint8_t i = 0; i < sizeof(encoded); i++) Serial.write(encoded[i]);
}