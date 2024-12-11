/*
Deterministic Function Generator Firmware

Electric Vehicle Capstone Research Team
Florida Institute of Technology Department of Electrical and Computer Engineering

Contributors : Derek May, Shawn Steakley, Elis Karcini, Alejandro Loynaz Ceballos

Last Updated : Fall 2024 

MIT License

Copyright (c) [2024] [Derek May]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// Include(s)
#include <SPI.h>

// 0%-100% Scaled Sine LUT with precision 256
const uint8_t sine256[100][256] PROGMEM =
{
// ...
// 100 LINES OF RAW DATA OMITTED FOR BREVITY AND READABILITY. FULL CODE WILL BE ATTACHED ELSEWHERE.
// ...
};
uint8_t sine256tmp[256] = {0};

// Output Pins
#define PWM1 3        // Phase 1 = OC2B
#define PWM2 9        // Phase 2 = OC1A
#define PWM3 0        // Phase 3 = OC1B
#define SCK_PIN   13  // D13 = pin19 = PortB.5
#define MISO_PIN  12  // D12 = pin18 = PortB.4
#define MOSI_PIN  11  // D11 = pin17 = PortB.3
#define SS_PIN    10  // D10 = pin16 = PortB.2

// Phase Shifts
const int Phase2Offset = 256 / 3;       // 120° phase shift
const int Phase3Offset = (256 * 2) / 3; // 240° phase shift

int freqPercent               = 0;        // Default percentage of the maximum frequency
double OutputFrequency        = 0.0;      // Default frequency in Hz
double MaximumFrequency       = 3000.0    // Maximum frequency in Hz
const double CarrierFrequency = 31376.6;  // Carrier frequency in Hz

// Information about how and why the tuning value is calculated like this is from NHM 2009 / Martin Nawrath
// https://interface.khm.de/index.php/lab/interfaces-advanced/arduino-dds-sinewave-generator/index.html
volatile unsigned long TuningValue;
volatile unsigned long TuningValueMax = pow(2, 32) * MaximumFrequency / CarrierFrequency;

// Timer Setup Procedure
// To get MaximumFrequency we need TOP = (16 MHz / MaximumFrequency / prescale / 2) - 1 = 159
void Setup_timers(void)
{
  // Timer 1 setup
  // WGM=8 Phase/Frequency Correct PWM with TOP in ICR1
  TCCR1A = 0;                           // Clear Timer/Counter Control Register 1A
  TCCR1B = 0;                           // Clear Timer/Counter Control Register 1B
  TIMSK1 = 0;                           // Disable all Timer1 interrupts
  ICR1 = 159;                           // TOP value = 159
  TCCR1A |= _BV(COM1A1) | _BV(COM1B1);  // Enable PWM on A and B
  TCCR1B |= _BV(WGM13) | _BV(CS10);     // WGM = 8, Prescale = 1

  // Timer 2 setup
  // WGM=5 Phase Correct PWM with TOP in OCR2A
  TCCR2A = 0;                           // Clear Timer/Counter Control Register 2A
  TCCR2B = 0;                           // Clear Timer/Counter Control Register 2B
  TIMSK2 = 0;                           // Disable all Timer2 interrupts
  OCR2A = 159;                          // TOP value = 159
  TCCR2A |= _BV(COM1B1);                // Enable PWM on B only. (OCR2A holds TOP)
  TCCR2A |= _BV(WGM20);                 // WGM = 5
  TCCR2B |= _BV(WGM22) | _BV(CS20);     // WGM = 5, Prescale = NONE
  TIMSK2 |= _BV(TOIE2);                 // Enable Timer2 Overflow Interrupt
}

void setup()
{
  // Define Outputs
  pinMode(PWM1, OUTPUT);
  pinMode(PWM2, OUTPUT);
  pinMode(PWM3, OUTPUT);
  pinMode(MISO_PIN, OUTPUT);  // Set MISO as OUTPUT (required for SPI slave)
  pinMode(MOSI_PIN, INPUT);   // MOSI as INPUT (master out, slave in)
  pinMode(SCK_PIN, INPUT);    // SCK as INPUT (clock from master)
  pinMode(SS_PIN, INPUT);     // SS as INPUT (to know when selected as slave)

  // Configure SPI
  SPCR |= _BV(SPE);           // Enable SPI in slave mode
  SPI.attachInterrupt();      // Enable SPI interrupt

  // Setup Timers
  TuningValue = pow(2, 32) * OutputFrequency / CarrierFrequency;
  Setup_timers();
}

// Timer 2 Interrupt
// Runs every 1/CarrierFrequency seconds
ISR(TIMER2_OVF_vect)
{
  static uint32_t phase_accumulator = 0;
  phase_accumulator += TuningValue;
  uint8_t current_count = phase_accumulator >> 24;
  OCR2B = pgm_read_byte_near(sine256[freqPercent] + current_count);
  OCR1A = pgm_read_byte_near(sine256[freqPercent] + (uint8_t)(current_count + Phase2Offset));
  OCR1B = pgm_read_byte_near(sine256[freqPercent] + (uint8_t)(current_count + Phase3Offset));
}

// SPI Interrupt
// Runs whenever data has been received over SPI
ISR(SPI_STC_vect) { freqPercent = SPDR; }

void loop() {
  OutputFrequency = (int)(((freqPercent * MaximumFrequency) / 100.0));
  TuningValue = pow(2, 32) * OutputFrequency / CarrierFrequency;
  delay(5);    
}
