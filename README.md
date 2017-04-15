# RepetierLights
Arduino/Led project to illuminate a 3d printer and provide status information from Repetier Server

The project has 3 strips of neopixels, to prividing white light to the workspace, the third providing a display mounted to a cabinet

The project comprises two major parts, Arduino hardware/software, and python scripts running on the host.

The python scripts (`debian` folder) query repetier server via api, and sends commands via serial to update the led display.

The arduino manages a few tasks, displaying output according to the python scripts commands, illuminating the workspace, brightening or darkening it based on a door switch, and provides buttons to allow the user to adjust light brightness.

Installtion requires building the arduino circuit, programming the arduino (`RepetierLights.ino`), installing the software on ubuntu/debian (`repetierlights_0.1.deb` provided) and configuring the software (`/etc/repetierLights.py`).

```
                                   ╔═══════╗                ╔═══════════╗
                                   ║  PC   ║                ║ 5v supply ║
                                   ╚══╤╤═══╝                ╚════╤═╤════╝
                                  USB ││    ┌────────────────────┤ │
                                    ╔═╧╧════╧═╗            GND   │ │
                                 2  ║         ║  4 ┌────────┐    ├C┤apacitor (1000uF)
                             ┌─────>D         D>───┤  330R  ├────│┐│
                      Door   o      ║         ║  3 └────────┘    ┢┷┪
                      Switch  /     ║         D>──LED Strip 2    ┃ ┃ LED
                 +5          o      ║         ║  5               ┃o┃ Strip 1
                  ┯          │      ║         D>──LED Strip 3    ┃ ┃
                 ┌┴┐         ┷      ║ Arduino ║                  ┃o┃
                 │R│        GND     ║         ║                  ┃ ┃
                 └┬┘             0  ║         ║                  ┃o┃
    ┌─────────────┼────────────────>A         ║                  ┃ ┃
    o            ┌┴┐                ║         ║                  ┇ ┇
     /           │R│                ║         ║                  ┇ ┇
    o            └┬┘                ║         ║                  ┋ ┋
    │      ┌──────┤                 ╚═════════╝
    ┷      o     ┌┴┐
   GND      /    │R│
           o     └┬┘
           │      │      Resistors approx 570 (to 5v)
           ┷      o                approx 330 and 330 (to GND)
          GND      /
                  o
 Push Buttons     │
                  ┷
                 GND
```