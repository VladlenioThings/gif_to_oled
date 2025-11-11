#include <U8g2lib.h>//https://github.com/olikraus/u8g2

#include <SdFat.h>//https://github.com/greiman/SdFat
#include <Wire.h>

//#include <TimeProfiler.h>//https://github.com/hideakitai/TimeProfiler

#define I2C1_SDA RX
#define I2C1_SCL D3
#define SD_CS D8

#define FRAME_WIDTH 128
#define FRAME_HEIGHT 64

#define FRAME_DELAY_MS 12         // задержка между кадрами (если 0, то получается примерно 20-21мс) при u8g2.setBusClock(800000);

#define RAW_FILE "bad_apple_480_360_fit.raw"
/*
gears_fit_invert_th_200_5.raw
bad_apple_480_360_fit.raw
bad_apple_480_360_stretch.raw
cat_threshold_200_fit_invert.raw
cat_threshold_200_stretch_invert.raw
yinyan_fit.raw
yinyan_stretch.raw
*/

#define FRAME_SIZE_BYTES (FRAME_WIDTH * FRAME_HEIGHT / 8)

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
SdFat SD;
SdFile animFile;
uint8_t buf[FRAME_SIZE_BYTES];

void setup() {
//Serial.begin(115200, SERIAL_8N1, SERIAL_TX_ONLY);
Wire.begin(I2C1_SDA, I2C1_SCL);

u8g2.begin();
u8g2.setBusClock(800000);
u8g2.setFont(u8g2_font_5x8_mr);

if (!SD.begin(SD_CS, SD_SCK_MHZ(20))) while(1);
if (!animFile.open(RAW_FILE, O_READ)) while(1);
}

void loop() {
//TIMEPROFILE_BEGIN(all);

uint32_t totalBytes = animFile.fileSize();
uint32_t totalFrames = totalBytes / FRAME_SIZE_BYTES;
uint32_t lastFrameMs = 0; // время предыдущего кадра
	/*
	{
	SCOPED_TIMEPROFILE(all);
	*/
	for (uint32_t frame = 0; frame < totalFrames; frame++) {
		uint32_t frameStart = millis();

		animFile.seekSet(frame * FRAME_SIZE_BYTES);
		animFile.read(buf, FRAME_SIZE_BYTES);

		u8g2.drawXBMP(0, 0, FRAME_WIDTH, FRAME_HEIGHT, buf);

		// показываем время предыдущего кадра
		int x = 0, y = 0, h = 8;
		static char str[8];
		snprintf(str, sizeof(str), "%lums", lastFrameMs); 
		u8g2.drawStr(x, h-1, str);

		u8g2.sendBuffer();

		// задержка между кадрами
		if (FRAME_DELAY_MS > 0) delay(FRAME_DELAY_MS);

		yield(); // чтобы watchdog не сработал

		// измеряем реальное время текущего кадра
		lastFrameMs = millis() - frameStart;
		}
	/*
	}
TIMEPROFILE_END(all);

unsigned long ms = TimeProfiler.getProfile("all");
unsigned long minutes = ms / 60000;
unsigned long seconds = (ms % 60000) / 1000;

Serial.print("all animation time: ");
Serial.print(minutes);
Serial.print(":");
if (seconds < 10) Serial.print("0");
Serial.println(seconds);
*/
animFile.seekSet(0); // зацикливание
}

