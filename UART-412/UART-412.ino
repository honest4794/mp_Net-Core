//   ----\_/----
//  | VCC   GND |
//  | PA6   PA3 |
//  | PA7   PA0 |
//  | PA1   PA2 |
//   -----------       attiny412
#include <Arduino.h>
#define F_CPU 20000000UL // Ensure this matches your clock speed
#include <util/delay.h>
#define ADDR        1

#define PWM_INPUT_PIN PIN_PA1 
#define IN1_PIN PIN_PA2 // Motor Direction/PWM
#define IN2_PIN PIN_PA3 // Motor Direction/PWM

#define MAX_DEVICE  32
#define HEADER      0xFF
#define ENDING      0xFE
#define PERIOD 102  //9600
//#define PERIOD 51   //19200

uint8_t value;

void setup() {
  noInterrupts();
  pinMode(PWM_INPUT_PIN, INPUT_PULLUP);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
}

void updateMotor(int value) {
  // Dead zone for stop: 45% - 55%
  if (value < 128) {
    analogWrite(IN2_PIN, 0);
    analogWrite(IN1_PIN, (127 - value)*2);
  } else {
    analogWrite(IN1_PIN, 0);
    analogWrite(IN2_PIN, (value-128)*2);
  }
}

void get_value() {
  uint8_t i;

  while (PORTA.IN & PIN1_bm);
  _delay_us(PERIOD*3/2);
  for (i=0 ; i<8 ; i++) {
    value = value >> 1;
    if (PORTA.IN & PIN1_bm)
      value+=0x80;
    _delay_us(PERIOD);
  }
}

void loop() {
  uint8_t result, i;
  if (!(PORTA.IN & PIN1_bm)) {
//HEADER
    get_value();
    if (value == HEADER) {
//ADDR
      get_value();
      if (value == ADDR) {
//VALUE
        get_value();
        updateMotor(value);
      } else if (value == 0x00) {
        i = 1;
        while((value != ENDING) && (i < (MAX_DEVICE+2))) {
          get_value();
          if (i == ADDR)
            result = value;
          i++;            
        }
        updateMotor(result);
      }
    }
  }
}
