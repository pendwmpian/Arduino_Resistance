#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;  /* Use this for the 16-bit version */
// Adafruit_ADS1015 ads;     /* Use this for the 12-bit version */

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

  Serial.println("ADC Range: +/- 6.144V (1 bit = 3mV/ADS1015, 0.1875mV/ADS1115)");

  // The ADC input range (or gain) can be changed via the following
  // functions, but be careful never to exceed VDD +0.3V max, or to
  // exceed the upper and lower limits if you adjust the input range!
  // Setting these values incorrectly may destroy your ADC!
  //                                                                ADS1015  ADS1115
  //                                                                -------  -------
  ads.setGain(GAIN_TWOTHIRDS);  // 2/3x gain +/- 6.144V  1 bit = 3mV      0.1875mV (default)
  // ads.setGain(GAIN_ONE);        // 1x gain   +/- 4.096V  1 bit = 2mV      0.125mV
  // ads.setGain(GAIN_TWO);        // 2x gain   +/- 2.048V  1 bit = 1mV      0.0625mV
  // ads.setGain(GAIN_FOUR);       // 4x gain   +/- 1.024V  1 bit = 0.5mV    0.03125mV
  // ads.setGain(GAIN_EIGHT);      // 8x gain   +/- 0.512V  1 bit = 0.25mV   0.015625mV
  // ads.setGain(GAIN_SIXTEEN);    // 16x gain  +/- 0.256V  1 bit = 0.125mV  0.0078125mV

  ads.setDataRate(RATE_ADS1115_860SPS);

  if (!ads.begin()) {
    while (1){
        Serial.println("Failed to initialize ADS.");
    }
  }
}


void loop(void)
{
  Data result;
  uint8_t encoded[sizeof(Data) + 2];

  /* Be sure to update this value based on the IC and the gain settings! */
  //float   multiplier = 3.0F;    /* ADS1015 @ +/- 6.144V gain (12-bit results) */
  //float multiplier = 0.1875F; /* ADS1115  @ +/- 6.144V gain (16-bit results) */
  //float R0 = 390.0F;
  //float gain = 1.0F + (100000.0F / R0);

  result.volt = ads.readADC_SingleEnded(0);
  //Serial.println(micros());
  result.time = micros();
  encodeCOBS(&result, encoded);
  for(uint8_t i = 0; i < sizeof(encoded); i++) Serial.write(encoded[i]);

  //Serial.println(micros()); //Serial.print(" "); Serial.println(String(results * multiplier / gain, 6));

  //delay(20);
}