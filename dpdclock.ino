#include <SoftwareSerial.h>

#define LTX 5
#define LRX -1 // i dont need ts
#define BAUD 9600
#define CLS 231

SoftwareSerial vfd(LRX, LTX);

const byte cl_startc = 0x02;
const byte cl_endc   = 0x03;

char c_rbuf[41]; 
uint8_t c_rind = 0;
bool c_recv = false;

inline uint8_t eD(uint8_t x) {
  asm volatile (
    "LSL %0 \n\t" 
    "ADC %0,r1 \n\t" // just... uhm... just don't fucking look at me like that, this shit works and idc
    "COM %0 \n\t"
    :"+r" (x)
  );
  return x;
} /*why not the -O2 or -Os? because shut the fuck up, sweetie~*/


void printR(const char* t) {
  while (*t) {
    vfd.write(eD((uint8_t)*t));
    t++;
  }
}

void setup() {
  Serial.begin(BAUD);
  vfd.begin(BAUD);
  vfd.write(CLS); 
}

void loop() {
  while (Serial.available() > 0) {
    byte b = Serial.read();

    if (b == cl_startc) {
      c_recv = true;
      c_rind = 0;
    } 
    else if (b == cl_endc) {
      if (c_recv) {
        c_rbuf[c_rind] = '\0';
        vfd.write(CLS); 
        printR(c_rbuf);
        c_recv = false;
      }
    } 
    else if (c_recv) {
      if (c_rind < 40) {
        c_rbuf[c_rind++] = (char)b; 
      }            
    }
  }        
}
// wah
