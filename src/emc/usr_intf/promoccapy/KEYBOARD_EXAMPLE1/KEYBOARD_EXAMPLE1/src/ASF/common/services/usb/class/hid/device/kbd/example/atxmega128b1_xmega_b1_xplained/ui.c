/**
 * \file
 *
 * \brief User Interface
 *
 * Copyright (c) 2011-2015 Atmel Corporation. All rights reserved.
 *
 * \asf_license_start
 *
 * \page License
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. The name of Atmel may not be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * 4. This software may only be redistributed and used in connection with an
 *    Atmel microcontroller product.
 *
 * THIS SOFTWARE IS PROVIDED BY ATMEL "AS IS" AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT ARE
 * EXPRESSLY AND SPECIFICALLY DISCLAIMED. IN NO EVENT SHALL ATMEL BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * \asf_license_stop
 *
 */
/*
 * Support and FAQ: visit <a href="http://www.atmel.com/design-support/">Atmel Support</a>
 */

#include <asf.h>
#include "ui.h"

#define F_CPU 48000000
#include <util/delay.h>

//! Sequence process running each \c SEQUENCE_PERIOD ms
#define SEQUENCE_PERIOD 5

struct hid_seq{
	bool b_modifier;
	bool b_down;
	uint8_t u8_value;
}; 
struct hid_seq ui_sequence[20];

int k=0;	//stevec za ui_sequence 

//matrika
#define N_ROWS 5
#define N_COLS 13
#define ALT_FN_ROW 4  //tipka za izbiro "alternate" tabel
#define ALT_FN_COL 0

static uint8_t keypad_layout[N_ROWS][N_COLS]={
	 {HID_CAPS_LOCK, HID_X, HID_Y, HID_Z, HID_M, HID_G, HID_F, HID_7, HID_8, HID_9, HID_C, HID_X, HID_V},
     {0, HID_A, HID_B, HID_C, HID_O, HID_R, HID_S, HID_4, HID_5, HID_6, HID_HOME, HID_UP, HID_PAGEUP },
	 {0, HID_I, HID_J, HID_K, HID_P, HID_Q, HID_T, HID_1, HID_2, HID_3, HID_LEFT, 0, HID_RIGHT},
     {HID_DELETE, HID_COLON, HID_COMMA, HID_PLUS, HID_KEYPAD_DIVIDE, HID_KEYPAD_MULTIPLY, HID_KEYPAD_PLUS, HID_KEYPAD_MINUS, HID_0, HID_DOT, HID_END, HID_DOWN, HID_PAGEDOWN },
     {0, 0, 0, 0, HID_SPACEBAR, 0, HID_BACKSPACE, 0, 0, 0, HID_ESCAPE, 0 , HID_ENTER}	 
};

static uint8_t keypad_modifiers[N_ROWS][N_COLS]={	
	{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, HID_MODIFIER_LEFT_CTRL, HID_MODIFIER_LEFT_CTRL, HID_MODIFIER_LEFT_CTRL},
    {HID_MODIFIER_LEFT_CTRL},
    {HID_MODIFIER_LEFT_ALT,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, HID_MODIFIER_RIGHT_SHIFT, 0},
    {0, 0, HID_MODIFIER_RIGHT_SHIFT},
    {0}		
};
	
static uint8_t keypad_alternate_layout[N_ROWS][N_COLS]={
	{HID_CAPS_LOCK, HID_U, HID_V, HID_W, HID_N, HID_H, HID_E, HID_7, HID_8, HID_9, HID_C, HID_X, HID_V},
	{0, HID_2, HID_6, HID_D, HID_9, HID_0, HID_QUOTE, HID_4, HID_5, HID_6, HID_HOME, HID_UP, HID_PAGEUP},
	{0, HID_OPEN_BRACKET, HID_CLOSE_BRACKET, HID_L, HID_7, HID_1, HID_UNDERSCORE, HID_1, HID_2, HID_3, HID_LEFT, 0, HID_RIGHT},
	{HID_DELETE, HID_COLON, HID_DOT, HID_COMMA, HID_3, HID_SLASH, HID_5, HID_KEYPAD_MINUS, HID_0, HID_DOT, HID_END, HID_DOWN, HID_PAGEDOWN},		
    {0, 0, 0, 0, HID_SPACEBAR, 0, HID_BACKSPACE, 0, 0, 0, HID_ESCAPE, 0 , HID_ENTER}
};

static uint8_t keypad_alternate_modifiers[N_ROWS][N_COLS]={
    {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, HID_MODIFIER_LEFT_CTRL, HID_MODIFIER_LEFT_CTRL, HID_MODIFIER_LEFT_CTRL},
    {HID_MODIFIER_LEFT_CTRL, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, 0, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT},
    {HID_MODIFIER_LEFT_ALT, 0, 0, 0, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT},
	{0, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, 0, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, HID_MODIFIER_RIGHT_SHIFT, 0, 0, 0, 0, 0, 0},
	{0}
};

uint8_t keypress_state[N_ROWS][N_COLS]={0};
#define FN 1
#define ALT_FN 2


uint8_t keypad_rows[N_ROWS]={IOPORT_CREATE_PIN(PORTA,0),
							IOPORT_CREATE_PIN(PORTA,1),
							IOPORT_CREATE_PIN(PORTA,2),
							IOPORT_CREATE_PIN(PORTA,3),
							IOPORT_CREATE_PIN(PORTA,4)};

uint8_t keypad_columns[N_COLS]={IOPORT_CREATE_PIN(PORTC,4),
							   IOPORT_CREATE_PIN(PORTC,5),
							   IOPORT_CREATE_PIN(PORTC,6),
							   IOPORT_CREATE_PIN(PORTC,7),
							   IOPORT_CREATE_PIN(PORTD,0),
							   IOPORT_CREATE_PIN(PORTD,1),
							   IOPORT_CREATE_PIN(PORTD,2),
							   IOPORT_CREATE_PIN(PORTD,3),
							   IOPORT_CREATE_PIN(PORTD,4),
							   IOPORT_CREATE_PIN(PORTD,5),
							   IOPORT_CREATE_PIN(PORTE,0),
							   IOPORT_CREATE_PIN(PORTE,1),
							   IOPORT_CREATE_PIN(PORTE,2)};
					
uint8_t PIN_C3 = IOPORT_CREATE_PIN(PORTC,3); //backspace tipka
uint8_t LED_0  = IOPORT_CREATE_PIN(PORTC,1);
uint8_t LED_1  = IOPORT_CREATE_PIN(PORTC,2);

//softkeys
#define N_V_SK 6
#define N_H_SK 10
static uint16_t v_sk_tolerance = 5;
static uint16_t h_sk_tolerance = 5;
									//vsi upori na glavnem vezju 12k
									//vsi upori na softeyih 1k2
static uint16_t v_sk_val[N_V_SK]={35, 55, 73, 90, 107, 123};	// lemut{35, 58, 79, 99, 119, 139};
static uint16_t h_sk_val[N_H_SK]={30, 46, 60, 74, 86, 98, 110, 123, 135, 148};	// lemut {31, 48, 65, 80, 96, 111, 126, 141, 156, 172};
static uint16_t v_sk_no_key = 20;
static uint16_t h_sk_no_key = 20;
static uint8_t v_sk_f[N_V_SK+1]={HID_F6,HID_F5,HID_F4,HID_F3,HID_F2,HID_F1,0};
static uint8_t h_sk_f[N_H_SK+1]={HID_F10,HID_F9,HID_F8,HID_F7,HID_F6,HID_F5,HID_F4,HID_F3,HID_F2,HID_F1,0};
static uint8_t v_sk_modifiers[N_V_SK+1]={HID_MODIFIER_LEFT_SHIFT,HID_MODIFIER_LEFT_SHIFT,HID_MODIFIER_LEFT_SHIFT,HID_MODIFIER_LEFT_SHIFT,HID_MODIFIER_LEFT_SHIFT,HID_MODIFIER_LEFT_SHIFT,0};
static uint8_t h_sk_modifiers[N_H_SK+1]={0};

int v_sk_state=0;
int h_sk_state=0;

uint8_t ADC_PIN0  = IOPORT_CREATE_PIN(PORTA,5);
uint8_t ADC_PIN1  = IOPORT_CREATE_PIN(PORTA,6);

//
volatile int enter_bootloader=0;
void(* start_bootloader)(void) = (void (*)(void))(BOOT_SECTION_START/2+0x1FC/2);
void ask_enter_bootloader(void){
	if(enter_bootloader){
		udc_stop();
		EIND = BOOT_SECTION_START>>17;
		start_bootloader();
	}
}

void ui_init(void)
{
	for(int i=0; i<N_ROWS;i++){  //vrstice so vhodi
		ioport_set_pin_dir(keypad_rows[i], IOPORT_DIR_INPUT);
		ioport_set_pin_mode(keypad_rows[i], IOPORT_MODE_PULLUP);
	}
	
	for(int i=0; i<N_COLS; i++){  //stolpci pa izhodi
		ioport_set_pin_dir(keypad_columns[i], IOPORT_DIR_OUTPUT);
		ioport_set_pin_level(keypad_columns[i], 1);
	}
	
	ioport_set_pin_dir(PIN_C3, IOPORT_DIR_INPUT);
	ioport_set_pin_mode(PIN_C3, IOPORT_MODE_PULLUP);
	ioport_set_pin_dir(LED_0, IOPORT_DIR_OUTPUT);
	ioport_set_pin_level(LED_0, 0);
	ioport_set_pin_dir(LED_1, IOPORT_DIR_OUTPUT);
	ioport_set_pin_level(LED_1, 0);
	
	PR.PRPA = 0x05; //Power on adc
	ADCA.CTRLA = ADC_ENABLE_bm ; // Enable the ADC
	ADCA.CTRLB = 0x04; //8 bit 
	ADCA.REFCTRL = 0x10; // vcc ref
	ADCA.EVCTRL = 0 ; // no events
	ADCA.PRESCALER = ADC_PRESCALER_DIV64_gc ;
	ADCA.CH0.CTRL = ADC_CH_GAIN_1X_gc | 0x01 ; // Gain = 1, Single Ended
	ADCA.CH0.INTCTRL = 0 ; // No interrupt
	ioport_set_pin_dir(ADC_PIN0, IOPORT_DIR_INPUT);
	ioport_set_pin_dir(ADC_PIN1, IOPORT_DIR_INPUT);	
}//ui_init

uint16_t ReadADC(uint8_t Channel){ 
    ADCA.CH0.MUXCTRL = (Channel<<3);
	ADCA.CH0.CTRL |= ADC_CH_START_bm; // Start conversion
	_delay_ms(1); //while(ADCA.INTFLAGS==0) ; // Wait for complete - raje uporabljam delay
	ADCA.INTFLAGS = ADCA.INTFLAGS ;
    return ADCA.CH0RES ;	
}

void usb_hid_sprint(int val, struct hid_seq *ui_sequence){
	int val_[]={val/1000, (val%1000)/100, (val%100)/10, (val%10)};
	int k=0;
	for(int a=0; a<4; a++){
			ui_sequence[k].b_modifier = false;
			ui_sequence[k].u8_value = (val_[a] > 0) ? HID_1 + val_[a] - 1 : HID_0;
			ui_sequence[k++].b_down = 1;
			ui_sequence[k].b_modifier = false;
			ui_sequence[k].u8_value = (val_[a] > 0) ? HID_1 + val_[a] - 1 : HID_0;
			ui_sequence[k++].b_down = 0;		
	}
	ui_sequence[k].b_modifier = false;
	ui_sequence[k].u8_value = HID_COMMA;
	ui_sequence[k++].b_down = 1;
	ui_sequence[k].b_modifier = false;
	ui_sequence[k].u8_value = HID_COMMA;
	ui_sequence[k++].b_down = 0;
}

void ui_powerdown(void)
{

}

void ui_wakeup_enable(void)
{
	PORT_t *port;
	// Configure pin change interrupt for asynch. wake-up on button pin.
	ioport_configure_pin(GPIO_PUSH_BUTTON_0,
			IOPORT_DIR_INPUT | IOPORT_PULL_UP);
	port = ioport_pin_to_port(GPIO_PUSH_BUTTON_0);
	port->INT0MASK = 0x01;
	port->INTCTRL = PORT_INT0LVL_LO_gc;
}

void ui_wakeup_disable(void)
{
	PORT_t *port;
	port = ioport_pin_to_port(GPIO_PUSH_BUTTON_0);
	port->INT0MASK = 0x00;
}


/*! \brief Interrupt on "pin change" from switch to do wakeup on USB
 * Callback running when USB Host enable mouse interface
 *
 * Note:
 * This interrupt is enable when the USB host enable remotewakeup feature
 * This interrupt wakeup the CPU if this one is in idle mode
 */
ISR(PORTE_INT0_vect)
{
	/*
	PORT_t *port;
	port = ioport_pin_to_port(GPIO_PUSH_BUTTON_0);
	port->INTFLAGS = 0x01; // Ack interrupt
	// It is a wakeup then send wakeup USB
	udc_remotewakeup();
	*/
}

void ui_wakeup(void)
{
	/*
	LED_On(LED0_GPIO);
	led_power_on();
	*/
}



void ui_process(uint16_t framenumber)
{
	bool b_btn_state, sucess, b_PC3_btn_state;
	static bool b_PC3_btn_last_state = false;
	static bool sequence_running = false;
	static uint8_t u8_sequence_pos = 0;
	uint8_t u8_value;
	static uint16_t cpt_sof = 0;
	
	
		// Scan process running each 2ms
		cpt_sof++;
		if ((cpt_sof % 2) == 0) {
			return;
		}
  
  
  		//skeniram matriko
  		if(!sequence_running){ //poèaka da je prejšnja sekvenca poslana
	  		for(int i=0; i<N_COLS; i++){	//postavlja posamezne izhode na stolpcih na 0
		  		ioport_set_pin_level(keypad_columns[i], 0);
		  		for(int j=0;j<N_ROWS;j++){	//bere stanje vrstic na vhodih
			  		b_btn_state=!ioport_get_pin_level(keypad_rows[j]);
			  		if (b_btn_state && keypress_state[j][i]==0) //pozitivna flanka
			  		{
						sequence_running=true;
				  		if (keypress_state[ALT_FN_ROW][ALT_FN_COL] > 0){
					  		keypress_state[j][i] = ALT_FN;
					  		if (keypad_alternate_modifiers[j][i])
					  		{
						  		ui_sequence[k].b_modifier = true;
						  		ui_sequence[k].u8_value = (keypad_alternate_modifiers[j][i]);
						  		ui_sequence[k++].b_down = true;
					  		}
					  		if(keypad_alternate_layout[j][i]){
						  		ui_sequence[k].b_modifier = false;
						  		ui_sequence[k].u8_value = (keypad_alternate_layout[j][i]);
						  		ui_sequence[k++].b_down = true;
					  		}
				  		}//alt_fn
				  		else{
					  		keypress_state[j][i] = FN;
					  		if(keypad_modifiers[j][i]){
						  		ui_sequence[k].b_modifier = true;
						  		ui_sequence[k].u8_value = (keypad_modifiers[j][i]);
						  		ui_sequence[k++].b_down = true;
					  		}
					  		if(keypad_layout[j][i]){
						  		ui_sequence[k].b_modifier = false;
						  		ui_sequence[k].u8_value = (keypad_layout[j][i]);
						  		ui_sequence[k++].b_down = true;
					  		}
				  		}
			  		}//pozitivna flanka
			  		else if (!b_btn_state && keypress_state[j][i]==FN )
			  		{
						sequence_running=true;
				  		keypress_state[j][i]=0;
				  		if(keypad_modifiers[j][i]){
					  		ui_sequence[k].b_modifier = true;
					  		ui_sequence[k].u8_value = (keypad_modifiers[j][i]);
					  		ui_sequence[k++].b_down = false;
				  		}
				  		if(keypad_layout[j][i]){
					  		ui_sequence[k].b_modifier = false;
					  		ui_sequence[k].u8_value = (keypad_layout[j][i]);
					  		ui_sequence[k++].b_down = false;
				  		}
			  		}//negativna flanka fn
			  		else if (!b_btn_state && keypress_state[j][i]==ALT_FN )
			  		{
						sequence_running=true;
				  		keypress_state[j][i]=0;
				  		if(keypad_alternate_modifiers[j][i]){
					  		ui_sequence[k].b_modifier = true;
					  		ui_sequence[k].u8_value = (keypad_alternate_modifiers[j][i]);
					  		ui_sequence[k++].b_down = false;
				  		}
				  		if(keypad_alternate_layout[j][i]){
					  		ui_sequence[k].b_modifier = false;
					  		ui_sequence[k].u8_value = (keypad_alternate_layout[j][i]);
					  		ui_sequence[k++].b_down = false;
				  		}
			  		}//negativna flanka altfn
		  		}//ROWS
		  		ioport_set_pin_level(keypad_columns[i], 1);
	  		}//COLS
  		}//sequence
  
  
	
    //dodatna tipka, vezana direktno na PORTC3
	if(!sequence_running){
		b_PC3_btn_state = !ioport_get_pin_level(PIN_C3);
		if (b_PC3_btn_state != b_PC3_btn_last_state) {
			b_PC3_btn_last_state = b_PC3_btn_state; 
			sequence_running = true;
			ui_sequence[k].b_modifier = false;
			ui_sequence[k].u8_value = keypad_layout[4][6]; //HID_BACKSPACE
			ui_sequence[k++].b_down = b_PC3_btn_state;
		}
	}
	
	
	//analogni horizontalni softkeyi
	int ad_h_sk=ReadADC(5);
	if (!sequence_running && h_sk_state==0){
		for(int i=0;i<N_H_SK;i++){
			if((h_sk_val[i] < (ad_h_sk + h_sk_tolerance)) && (h_sk_val[i] > (ad_h_sk - h_sk_tolerance)) ){
				if(h_sk_modifiers[i]){
					ui_sequence[k].b_modifier = true;
					ui_sequence[k].u8_value = (h_sk_modifiers[i]);
					ui_sequence[k++].b_down = true;
				}
				if(h_sk_f[i]){
					ui_sequence[k].b_modifier = false;
					ui_sequence[k].u8_value = (h_sk_f[i]);
					ui_sequence[k++].b_down = true;

					ui_sequence[k].b_modifier = false;
					ui_sequence[k].u8_value = (h_sk_f[i]);
					ui_sequence[k++].b_down = false;
				}
				if(h_sk_modifiers[i]){
					ui_sequence[k].b_modifier = true;
					ui_sequence[k].u8_value = (h_sk_modifiers[i]);
					ui_sequence[k++].b_down = false;
				}
				h_sk_state=1;
				sequence_running=true;
				break;
			}//if tol
		}//for i
	}//if seq h
	else if (ad_h_sk < h_sk_no_key) //key release event
	{
		h_sk_state=0;
	} //else seq h
	
	//analogni vertikalni softkeyi
	int ad_v_sk=ReadADC(6);
	if (!sequence_running && v_sk_state==0){
		for(int i=0;i<N_V_SK;i++){
			if((v_sk_val[i] < (ad_v_sk + v_sk_tolerance)) && (v_sk_val[i] > (ad_v_sk - v_sk_tolerance)) ){
				if(v_sk_modifiers[i]){
					ui_sequence[k].b_modifier = true;
					ui_sequence[k].u8_value = (v_sk_modifiers[i]);
					ui_sequence[k++].b_down = true;
				}
				if(v_sk_f[i]){
					ui_sequence[k].b_modifier = false;
					ui_sequence[k].u8_value = (v_sk_f[i]);
					ui_sequence[k++].b_down = true;
					
					ui_sequence[k].b_modifier = false;
					ui_sequence[k].u8_value = (v_sk_f[i]);
					ui_sequence[k++].b_down = false;
				}
				if(v_sk_modifiers[i]){
					ui_sequence[k].b_modifier = true;
					ui_sequence[k].u8_value = (v_sk_modifiers[i]);
					ui_sequence[k++].b_down = false;
				}		
				
				v_sk_state=1;
				sequence_running=true;
				break;
			}//if tol
		}//for i
	}//if seq v
	else if (ad_v_sk < v_sk_no_key) //key release event
	{
		v_sk_state=0;
	} //else seq v
	
	
	//test natipka vrednost ad
	/*
	if (keypress_state[4][12] && !sequence_running) {
		usb_hid_sprint( ReadADC(6), ui_sequence);
		k=10;
		sequence_running = true;
	}
	*/
		
	//ioport_set_pin_level(LED_1, 1);
	
    //pogoji za skok v bootloader
	/*
	if(!ioport_get_pin_level(PIN_C3)){	
     ioport_set_pin_level(LED_0, 1);
	 ioport_set_pin_level(LED_1, 0);
     enter_bootloader=1;	 
	}
	*/



	// Sequence process running each period
	if (SEQUENCE_PERIOD > cpt_sof) {
		return;
	}
	cpt_sof = 0;         

	if (sequence_running) {
		// Send next key
			//ioport_set_pin_level(LED_1, 1);
		u8_value = ui_sequence[u8_sequence_pos].u8_value;
		if (u8_value!=0) {
			if (ui_sequence[u8_sequence_pos].b_modifier) {
				if (ui_sequence[u8_sequence_pos].b_down) {
					sucess = udi_hid_kbd_modifier_down(u8_value);
				} else {
					sucess = udi_hid_kbd_modifier_up(u8_value);
				}
			} else {
				if (ui_sequence[u8_sequence_pos].b_down) {
					sucess = udi_hid_kbd_down(u8_value);
				} else {
					sucess = udi_hid_kbd_up(u8_value);
				}                          
			}
			if (!sucess) {
				return; // Retry it on next schedule
			}
		}
		// Valid sequence position
		u8_sequence_pos++;
		if (u8_sequence_pos >= k){
			//sizeof(ui_sequence) / sizeof(ui_sequence[0])) {
			u8_sequence_pos = 0;
			k=0;
			sequence_running = false;
			for(int l=0; l < sizeof(ui_sequence) / sizeof(ui_sequence[0]); l++) ui_sequence[l].u8_value = 0; //pobriše ui_seq
		}
		//ioport_set_pin_level(LED_1, 0);
	}
}


void ui_kbd_led(uint8_t value)
{
	if (value & HID_LED_NUM_LOCK) {
		//LED_On(LED2_GPIO);
	} else {
		//LED_Off(LED2_GPIO);
	}
	if (value & HID_LED_CAPS_LOCK) {
		//LED_On(LED3_GPIO);
	} else {
		//LED_Off(LED3_GPIO);
	}
}

/**
 * \defgroup UI User Interface
 *
 * Human interface on XMEGA-B1 Xplained:
 * - Led 0 and the RED led close to USB connector are on
 *   when USB line is in IDLE mode, and off in SUSPEND mode
 * - Led 1 blinks when USB host has checked and enabled HID Keyboard interface
 * - The led 2 displays numeric lock status.
 * - The led 3 displays caps lock status.
 * - The switch 0 open a note pad and send key sequence "Atmel AVR USB Keyboard"
 * - All switches can be used to wakeup USB Host in remote wakeup mode.
 */
