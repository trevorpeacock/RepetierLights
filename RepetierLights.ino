#include <FastLED.h>
#include <EEPROM.h>

#define NUM_LEDS         30

CRGB door_leds[NUM_LEDS];
CRGB light_leds[NUM_LEDS];

#define DOOR_SENSOR_DATA_DPIN 2
#define DOOR_LED_DATA_DPIN 4
#define LIGHT1_LED_DATA_DPIN 3
#define LIGHT2_LED_DATA_DPIN 5
#define BUTTON_PANEL_APIN 0

#define DOOR_FADE_SPEED 8
#define LIGHT_SCROLL_SPEED 8
byte light_brightness_open;
byte light_brightness_closed;

String commandqueue;
byte door_fade;
CRGB status_col;
CRGB status_col_background;
byte status_complete;

void read_eeprom() {
  light_brightness_open = EEPROM.read(0);
  light_brightness_closed = EEPROM.read(1);
}

void write_eeprom() {
  EEPROM.update(0, light_brightness_open);
  EEPROM.update(1, light_brightness_closed);
}

/*
 * base class, by default blanks all LEDs
 */
class Pattern {
  public:
    //This is called everytime the pattern starts to be used
    virtual void setup() {
    }
    //Called every frame. Pattern should be supplied to provided buffer
    virtual void update(CRGB ledbuffer[]) {
      for (int i = 0; i < NUM_LEDS; i++) {
        ledbuffer[i] = CRGB::Black;
      }
    }
};

class DoorPattern: public Pattern {

    int flow_position;

  public:
    DoorPattern() {
    }

    virtual void setup() {
      flow_position = 0;
    }

    virtual void update(CRGB ledbuffer[]) {
      int no_leds=map(status_complete, 0, 255, 0, NUM_LEDS-1);
      if(status_complete==0) no_leds=-1;
      //Serial.println(no_leds);
      for (int i = 0; i < NUM_LEDS; i++) {
        if(i<=no_leds) {
          ledbuffer[i]=status_col;
          if(i==(flow_position/2-1)) ledbuffer[i]*=2;
          if(i==(flow_position/2)) ledbuffer[i]*=4;
          if(i==(flow_position/2+1)) ledbuffer[i]*=2;
        } else {
          ledbuffer[i]=status_col_background;
        }
        ledbuffer[i].fadeToBlackBy(door_fade);
      }
      flow_position = (flow_position+1) % 200;
    }
};

class LightPattern: public Pattern {

    //int position;

  public:
    LightPattern() {
    }

    virtual void setup() {
      //position = 0;
    }

    virtual void update(CRGB ledbuffer[]) {
      //Pattern::update(ledbuffer);
      for (int i = 0; i < NUM_LEDS; i++) {
        ledbuffer[i]=CHSV(0, 0, map(door_fade, 0, 255, light_brightness_closed, light_brightness_open));
      //  ledbuffer[position % int(NUM_LEDS)] = CRGB::Red;
      }
      //position = (position + 1) % NUM_LEDS;
    }
};

DoorPattern doorpattern = DoorPattern();
LightPattern lightpattern = LightPattern();

void setup() {
  read_eeprom();
  status_col=CRGB::Green;
  status_col_background=CRGB::Black;
  status_complete=128;
  pinMode(DOOR_SENSOR_DATA_DPIN, INPUT_PULLUP);

  for(int i=0; i<NUM_LEDS; i++) {
    door_leds[i]=CRGB::Black;
    light_leds[i]=CRGB::Black;
  }
  FastLED.addLeds<NEOPIXEL, DOOR_LED_DATA_DPIN>(door_leds, NUM_LEDS);
  FastLED.addLeds<NEOPIXEL, LIGHT1_LED_DATA_DPIN>(light_leds, NUM_LEDS);
  FastLED.addLeds<NEOPIXEL, LIGHT2_LED_DATA_DPIN>(light_leds, NUM_LEDS);
  //FastLED.setMaxPowerInVoltsAndMilliamps(5,200);
  Serial.begin(9600);
  Serial.setTimeout(0);
  Serial.write("repetierLights\n");

  if(digitalRead(DOOR_SENSOR_DATA_DPIN)) {
    door_fade=255;
  } else {
    door_fade=0;
  }
}

void print_serial_string(String text) {
  for (int i = 0; i < text.length(); i++)
  {
    Serial.write(text[i]);   // Push each char 1 by 1 on each loop pass
  }
}
unsigned int count_string_instances(String s, char c) {
  unsigned int r = 0;
  for(int i = 0; i<s.length(); i++) {
    if(s.charAt(i)==c) r++;
  }
  return r;
}

String string_extract_numbers(String s, int count, byte b[]) {
  for(int i=0; i<count; i++) {
    int delim = s.indexOf(',');
    String num = s.substring(0, delim);
    s.remove(0, delim+1);
    //print_serial_string(s);
    //Serial.println();
    b[i]=num.toInt();
  }
  return s;
}

bool process_serial_command(String command) {
  if(count_string_instances(command, ',')!=6) return false;
  byte col[3];
  command=string_extract_numbers(command, 3, col);
  status_col=CHSV(int(col[0]), int(col[1]), int(col[2]));
  command=string_extract_numbers(command, 3, col);
  status_col_background=CHSV(int(col[0]), int(col[1]), int(col[2]));
  command=string_extract_numbers(command, 1, col);
  status_complete=col[0];
  return true;
}

void check_serial() {
  if(commandqueue.indexOf('\n')!=-1) {
    int linebreak = commandqueue.indexOf('\n');
    String command = commandqueue.substring(0, linebreak);
    commandqueue.remove(0, linebreak+1);
    //Serial.write('>');
    //print_string(Serial, command);
    //Serial.write('\n');
    if(!process_serial_command(command)) {
      Serial.write("repetierLights: Invalid Command\n");
    }
  }
}

void check_buttons() {
  int button = analogRead(BUTTON_PANEL_APIN);
  bool door_open = digitalRead(DOOR_SENSOR_DATA_DPIN);
  bool button1=false;
  bool button2=false;
  bool button3=false;
  if(button<140) { //280
    button3=true;
  } else if(button<360) { //440
    button2=true;
  } else if(button<730) {
    button1=true;
  }
  if(door_open) {
    if(door_fade<255) door_fade = min(255, door_fade + DOOR_FADE_SPEED);
    if(button1) {
      light_brightness_open = max(0, light_brightness_open - LIGHT_SCROLL_SPEED);
      write_eeprom();
    }
    if(button2) {
      light_brightness_open = min(255, light_brightness_open + LIGHT_SCROLL_SPEED);
      write_eeprom();
    }
  } else {
    if(door_fade>0) door_fade = max(0, door_fade - DOOR_FADE_SPEED);
    if(button1) {
      light_brightness_closed = max(0, light_brightness_closed - LIGHT_SCROLL_SPEED);
      write_eeprom();
    }
    if(button2) {
      light_brightness_closed = min(255, light_brightness_closed + LIGHT_SCROLL_SPEED);
      write_eeprom();
    }
  }
}

void loop() {
  check_buttons();
  doorpattern.update(door_leds);
  lightpattern.update(light_leds);
  FastLED.show();
  commandqueue = commandqueue + Serial.readString();
  check_serial();
  delay(33);
}
