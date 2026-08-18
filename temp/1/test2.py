# all_led_list[0][0].duty(2048)

# 0.5ms pulse = (0.5 / 20) * 4095 = 102
# 2.4ms pulse = (2.4 / 20) * 4095 = 491

for i in range(389):
    d = 102 +i
    all_led_list[0][1].duty(d)
    time.sleep_ms(10)
    
# for i in range(6226):
#     d = 1638 +i
#     led_list[0].led[0].duty_u16(d)
#     time.sleep_ms(10)