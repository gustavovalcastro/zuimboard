#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/adc.h" 
#include "esp_adc_cal.h"

#define ADC_CHANNEL ADC1_CHANNEL_0 

// Function to configure ADC for hall sensor reading
void configure_hall_read_pin(void)
{
    // Configuration
    adc1_config_width(ADC_WIDTH_BIT_DEFAULT);
    adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_12);

    // Calibration
    esp_adc_cal_characteristics_t adc1_chars;
    esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_DEFAULT, 0, &adc1_chars);
}

// Function to read hall sensor
int read_hall(void)
{
    return adc1_get_raw(ADC_CHANNEL);
}

#define HALL_MUX_VCC_1  GPIO_NUM_15
#define HALL_MUX_VCC_2  GPIO_NUM_2
#define HALL_MUX_VCC_3  GPIO_NUM_0

#define HALL_MUX_READ_1 GPIO_NUM_4
#define HALL_MUX_READ_2 GPIO_NUM_16
#define HALL_MUX_READ_3 GPIO_NUM_17

#define MAX_HALL_VCC_STATES 8
#define MAX_HALL_READ_STATES 8

void configure_hall_mux_pins(int hall_pin)
{
    gpio_config_t io_conf;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_OUTPUT;
    io_conf.pin_bit_mask = (1ULL << hall_pin);
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    gpio_config(&io_conf);
}

void configure_button_pins(int button_pin)
{
    gpio_config_t io_conf;
    io_conf.intr_type = GPIO_INTR_NEGEDGE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = (1ULL << button_pin);
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
    gpio_config(&io_conf);
}

void set_ios2zero()
{
    gpio_set_level(HALL_MUX_VCC_1, 0);
    gpio_set_level(HALL_MUX_VCC_2, 0);
    gpio_set_level(HALL_MUX_VCC_3, 0);

    gpio_set_level(HALL_MUX_READ_1, 0);
    gpio_set_level(HALL_MUX_READ_2, 0);
    gpio_set_level(HALL_MUX_READ_3, 0);
}

void set_gpio_vcc(uint8_t vcc_state)
{
    gpio_set_level(HALL_MUX_VCC_1, (vcc_state >> 0) & 0x01);
    gpio_set_level(HALL_MUX_VCC_2, (vcc_state >> 1) & 0x01);
    gpio_set_level(HALL_MUX_VCC_3, (vcc_state >> 2) & 0x01);
}

void set_gpio_read(uint8_t read_state)
{
    gpio_set_level(HALL_MUX_READ_1, (read_state >> 0) & 0x01);
    gpio_set_level(HALL_MUX_READ_2, (read_state >> 1) & 0x01);
    gpio_set_level(HALL_MUX_READ_3, (read_state >> 2) & 0x01);
}

void print_debug_squaresint(int hall_signals[MAX_HALL_VCC_STATES][MAX_HALL_READ_STATES])
{
    int rows[] = {1, 2, 3, 4, 5, 6, 7, 8};
    char columns[] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'};

    printf("\n--------------------------------------------------\n");
    for (int i = MAX_HALL_VCC_STATES - 1; i >= 0; i--) {
        for (int j = 0; j < MAX_HALL_READ_STATES; j++) {
            if (hall_signals[i][j] < 1150)
                printf("%c%d: %d  ", columns[j], rows[i], hall_signals[i][j]);
            else
                printf("%c%d: %d  ", columns[j], rows[i], hall_signals[i][j]);
        }
        printf("\n");
    }
    printf("--------------------------------------------------\n");
}

void print_squares(int hall_signals[MAX_HALL_VCC_STATES][MAX_HALL_READ_STATES])
{
    // Create new matrix
    char json_matrix[8][8];

    for (int i = MAX_HALL_VCC_STATES - 1; i >= 0; i--) {
        for (int j = 0; j < MAX_HALL_READ_STATES; j++) {
            if (hall_signals[i][j] < 1150) {
                json_matrix[i][j] = 'w';
            }
            else if (hall_signals[i][j] > 2000) {
                json_matrix[i][j] = 'b';
            }
            else {
                json_matrix[i][j] = ' ';
            }
        }
    }
    
    // New code: JSON Implementation (with linebreaks)
    char json_str[384];
    char *ptr = json_str;

    ptr += sprintf(ptr, "["); // no linebreak

    for (int i = MAX_HALL_VCC_STATES - 1; i >= 0; i--) {
        ptr += sprintf(ptr, "[");

        for (int j = 0; j < MAX_HALL_READ_STATES; j++) {
            ptr += sprintf(ptr, "\"%c\"", json_matrix[i][j]);
            if (j < 7) {
                ptr += sprintf(ptr, ",");
            }
        }

        ptr += sprintf(ptr, "]");
        if (i > 0) {
            ptr += sprintf(ptr, ","); // no linebreak
        }
    }

    ptr += sprintf(ptr, "]\n");

    printf("%s", json_str);
}

void sensor_task_2(void *pvParameter)
{
    int hall_signals[MAX_HALL_VCC_STATES][MAX_HALL_VCC_STATES];

    uint8_t vcc_state = 0;
    uint8_t read_state = 0;

    set_ios2zero();

    while(1) {
        set_gpio_vcc(vcc_state);
        set_gpio_read(read_state);

        vTaskDelay(10 / portTICK_PERIOD_MS);

        hall_signals[vcc_state][read_state] = read_hall();

        read_state++;
        if (read_state >= MAX_HALL_READ_STATES)
        {
            read_state = 0;
            vcc_state++;
            if (vcc_state >= MAX_HALL_VCC_STATES)
            {
                break;
            }
        }
    }

    print_squares(hall_signals);

    vTaskDelete(NULL);  // Delete the task when done
}

#include "esp_timer.h"

#define BUTTON_GPIO GPIO_NUM_5

#define DEBOUNCE_TIME_MS 2000

// Function to be executed in a new thread
void button_task(void *pvParameter)
{
    int task_id = (int)pvParameter;

    xTaskCreate(sensor_task_2, "sensor_task", 4096, NULL, 5, NULL);

    vTaskDelete(NULL);  // Delete the task when done
}

static void IRAM_ATTR gpio_isr_handler(void* arg)
{
    static uint64_t last_interrupt_time = 0;
    static int task_counter = 0;

    uint64_t current_time = esp_timer_get_time();
    uint64_t time_since_last = current_time - last_interrupt_time;

    if (time_since_last > DEBOUNCE_TIME_MS * 1000) { // Convert milliseconds to microseconds
        last_interrupt_time = current_time;

        task_counter++;
        xTaskCreate(button_task, "button_task", 4096, (void *)task_counter, 5, NULL);
    }
}

void app_main(void)
{
    // Configure hall sensor reading pin
    configure_hall_read_pin();

    // Configure hall sensor multiplexer pins
    configure_hall_mux_pins(HALL_MUX_VCC_1);
    configure_hall_mux_pins(HALL_MUX_VCC_2);
    configure_hall_mux_pins(HALL_MUX_VCC_3);

    configure_hall_mux_pins(HALL_MUX_READ_1);
    configure_hall_mux_pins(HALL_MUX_READ_2);
    configure_hall_mux_pins(HALL_MUX_READ_3);

    configure_button_pins(BUTTON_GPIO);

    gpio_install_isr_service(0);
    gpio_isr_handler_add(BUTTON_GPIO, gpio_isr_handler, (void*) BUTTON_GPIO);

}
