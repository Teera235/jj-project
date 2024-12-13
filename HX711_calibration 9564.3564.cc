#include "HX711.h"

const int LOADCELL_DOUT_PIN = 3;
const int LOADCELL_SCK_PIN = 2;

HX711 scale;

float calibration_factor = -9564.3564; 

void setup() {
  Serial.begin(9600);
  Serial.println("HX711 Calibration");

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  
  scale.set_scale(calibration_factor);
  scale.tare(); 

  Serial.println("Tare done! Remove all weight from scale.");
  delay(1);
  
  Serial.println("Place a known weight on the scale.");
}

void loop() {
  Serial.print((scale.get_units()/10), 3); 
  Serial.println();
  
  if (Serial.available()) {
    char temp = Serial.read();
    if (temp == '+') {
      calibration_factor += 1;
      Serial.print("Calibration Factor: ");
      Serial.println(calibration_factor);
      scale.set_scale(calibration_factor);
    }
    else if (temp == '-') {
      calibration_factor -= 1;
      Serial.print("Calibration Factor: ");
      Serial.println(calibration_factor);
      scale.set_scale(calibration_factor);
    }

  }

  delay(1);
}
