# from wave_library_list import *
# from lib.LEDMathMethod import *
# time.sleep_ms(1000)

debug =0
# only_led_io = [all_led_list[0][1]]
only_rgb_io = []

for i in rgb_list:
    for l in i:
        only_rgb_io.append(l)

# try:
#     if loop_one_success:
#         cfg.set_state('loop_one_success', False)
#         
#         while loop_one_success:
#                 ledC.run_Pattern([], run_time = 0, debug=debug)
#             pass
#         
#     else:
#         cfg.set_state('loop_one_success', False)
#         
#         
# except KeyboardInterrupt:
#     cfg.set_state('loop_one_success', False)


def wave_list_assign_next(led_no=1, pattern=[], speed=1,step=1,spacing=1, reverse=False ):
    """
    生成器函數,用於創建燈效模式
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 每個波形值重複的次數
        spacing: LED之間的間距(步進值)
        reverse: 是否反轉輸出
    Yields:
        list: 當前幀的LED亮度值列表
    """
    # 計算最大和最小亮度限制
    l_max = 0
    l_lim = 4095
    for i in pattern:
        t_l_max = i['l_max']
        t_l_lim = i['l_lim']

        l_max = l_max if t_l_max  < l_max else t_l_max
        l_lim = l_lim if t_l_lim  > l_lim else t_l_lim


        
    _wave_history_max = pattern[-1]['end_Time']
    
    # 獲取波形生成器
    _gen = ledC.mt.is_math_pattern_next(pattern,stop = True )
    
    # 初始化緩衝區 - 用於存儲每個LED的當前值
    _tempbuf = [l_lim] * led_no
    
    # 波形歷史記錄 - 存儲從生成器獲取的所有波形值
    _wave_history = list(_gen)
    
    # 當前步進位置
    _step_counter = 0
    
    while True:

        for i in range(led_no):
            # 計算該LED應該讀取的歷史索引
            _tempbuf[i] = _wave_history[((_step_counter* step   )+ (i* spacing))% _wave_history_max]
        
        # 根據speed參數重複輸出當前幀
        for _ in range(speed):
            if reverse:
                yield _tempbuf[::-1]
            else:
                yield _tempbuf.copy()  # 返回副本避免引用問題
        
        _step_counter = (_step_counter + 1)%_wave_history_max
        
def stepping_wave_next(led_no=1, pattern=[], speed=1,step=1, reverse=False ):
    """
    生成器函數,用於創建燈效模式
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 每個波形值重複的次數
        spacing: LED之間的間距(步進值)
        reverse: 是否反轉輸出
    Yields:
        list: 當前幀的LED亮度值列表
    """
    # 計算最大和最小亮度限制
    l_max = 0
    l_lim = 4095
    for i in pattern:
        t_l_max = i['l_max']
        t_l_lim = i['l_lim']

        l_max = l_max if t_l_max  < l_max else t_l_max
        l_lim = l_lim if t_l_lim  > l_lim else t_l_lim

        
    _wave_history_max = pattern[-1]['end_Time']
    
    # 獲取波形生成器
    _gen = ledC.mt.is_math_pattern_next(pattern,stop = True )
    
    # 初始化緩衝區 - 用於存儲每個LED的當前值
    _tempbuf = [l_lim] * led_no
    
    # 波形歷史記錄 - 存儲從生成器獲取的所有波形值
    _wave_history = list(_gen)
    
    # 當前步進位置
    _step_counter = 0
    
    while True:

        for i in range(led_no):
            # 計算該LED應該讀取的歷史索引
            for _buf in _wave_history[::step]:
                _tempbuf[i] = _buf
        
                # 根據speed參數重複輸出當前幀
                for _ in range(speed):
                    if reverse:
                        yield _tempbuf[::-1]
                    else:
                        yield _tempbuf.copy()  # 返回副本避免引用問題
                
                _step_counter = (_step_counter + 1)%_wave_history_max

def random_flash(in_led_io: list ,flash_io: int, flash_brightness: int, flash_duration : int, flash_gap_time: int, flash_no : int =1, rest_frame: int=0):
    
    flash_io = flash_io
    flash_brightness = flash_brightness
    flash_ = flash_duration
    flash_gap_time = flash_gap_time
    flash_no = flash_no
    rest_frame = rest_frame
    

    in_led_io = in_led_io

    rd_io = random_batch_generator(in_led_io, flash_io)
    run_time = 0
    gap_time = 0
    rd_io_list = next(rd_io)
    while 1:
        for _ in range(flash_no):
            if gap_time == 0: 
                if run_time == 0:
                    for i in rd_io_list:
                        i.set_buf(flash_brightness)
                        
                elif run_time == flash_-1:
                    for i in rd_io_list:
                        i.set_buf(0)
                    rd_io_list = next(rd_io)
            if gap_time == 0:
                run_time = (run_time +1)%flash_
            if run_time == 0:
                gap_time = (gap_time +1)%flash_gap_time
            yield

        for _ in range(rest_frame):
            yield
            
            
def random_flash_pattern_next(led_no=1, pattern=[], speed=1,spacing=1, reverse=False ):
    """
    生成器函數,用於創建燈效模式
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 每個波形值重複的次數
        spacing: LED之間的間距(步進值)
        reverse: 是否反轉輸出
    Yields:
        list: 當前幀的LED亮度值列表
    """
    # 計算最大和最小亮度限制

        
    _wave_history_max = pattern[-1]['end_Time']
    
    # 獲取波形生成器
    _gen = ledC.mt.is_math_pattern_next(pattern,stop = True )
    
    # 初始化緩衝區 - 用於存儲每個LED的當前值
    _tempbuf = [10] * led_no
    
    # 波形歷史記錄 - 存儲從生成器獲取的所有波形值
    _wave_history = list(_gen)
    
    # 當前步進位置
    _step_counter = 0
    
    rd_io = random_batch_generator(range(led_no), 1)
    
    while True:
        rd_io_list = next(rd_io)

        for i in _wave_history[::30]:
            # 計算該LED應該讀取的歷史索引
            _tempbuf[rd_io_list[0]] = i
        
            # 根據speed參數重複輸出當前幀
            for _ in range(speed):
                if reverse:
                    yield _tempbuf[::-1]
                else:
                    yield _tempbuf.copy()  # 返回副本避免引用問題
                    
                    
                    
def wave_list_assign_with_start_frame(led_no=1, pattern=[], speed=1, start_frames=None, reverse=False):
    """
    生成器函數,允許為每個LED指定不同的開始播放幀
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 每個波形值重複的次數
        start_frames: 每個LED的起始幀列表,例如 [0, 10, 20, 30, ...]
                     如果為None,則所有LED同時開始
                     如果長度小於led_no,會循環使用
        reverse: 是否反轉輸出
        
    Yields:
        list: 當前幀的LED亮度值列表
        
    Examples:
        # 每個LED間隔10幀開始
        gen = wave_list_assign_with_start_frame(
            led_no=8, 
            pattern=eyes_start, 
            start_frames=[0, 10, 20, 30, 40, 50, 60, 70]
        )
        
        # 自定義起始時間
        gen = wave_list_assign_with_start_frame(
            led_no=4,
            pattern=eyes_start,
            start_frames=[0, 50, 100, 150]  # 完全自定義
        )
    """
    # 計算波形總長度
    _wave_history_max = pattern[-1]['end_Time']
    
    # 獲取完整波形數據
    _gen = ledC.mt.is_math_pattern_next(pattern, stop=True)
    _wave_history = list(_gen)
    
    # 初始化緩衝區
    _tempbuf = [0] * led_no
    
    # 處理起始幀參數
    if start_frames is None:
        # 如果未指定,所有LED同時開始
        _start_frames = [0] * led_no
    else:
        # 確保起始幀列表長度匹配LED數量
        if len(start_frames) < led_no:
            # 循環填充
            _start_frames = [start_frames[i % len(start_frames)] for i in range(led_no)]
        else:
            _start_frames = start_frames[:led_no]
    
    # 全局幀計數器
    _global_frame = 0
    
    while True:
        for i in range(led_no):
            # 計算當前LED應該處於波形的哪個位置
            elapsed_frames = _global_frame - _start_frames[i]
            
            if elapsed_frames < 0:
                # 還未到達開始時間,保持暗態
                _tempbuf[i] = 0
            else:
                # 計算在波形歷史中的索引位置
                wave_index = elapsed_frames % _wave_history_max
                _tempbuf[i] = _wave_history[wave_index]
        
        # 根據speed參數重複輸出當前幀
        for _ in range(speed):
            if reverse:
                yield _tempbuf[::-1]
            else:
                yield _tempbuf.copy()
        
        # 全局幀計數器遞增
        _global_frame += 1


def wave_list_assign_with_delay(led_no=1, pattern=[], speed=1, delay=10, reverse=False):
    """
    便捷函數:自動生成等間隔延遲的起始幀
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 速度
        delay: 每個LED之間的延遲幀數
        reverse: 是否反轉
        
    Yields:
        list: LED亮度值列表
    """
    # 自動生成等間隔的起始幀列表
    start_frames = [i * delay for i in range(led_no)]
    
    # 調用主函數
    yield from wave_list_assign_with_start_frame(
        led_no=led_no,
        pattern=pattern,
        speed=speed,
        start_frames=start_frames,
        reverse=reverse
    )
    
    
def stepping_engine_list_next(led_no=1,pattern=[],pulse_list=[],reverse = False):
    # pulse_list = [(10,13),(10,2)]

    l_max = 0
    l_lim = 4095
    for i in pattern:
        t_l_max = i['l_max']
        t_l_lim = i['l_lim']

        l_max = l_max if t_l_max  < l_max else t_l_max
        l_lim = l_lim if t_l_lim  > l_lim else t_l_lim

    _gen = ledC.mt.is_math_pattern_next(pattern)

    io_no = led_no
    _tempbuf = [0]*(io_no)
    _stepping = 0
    while 1 :
        for pulse in pulse_list:
            l_run = next(_gen)
            for _ in range(pulse[1]):
                _tempbuf[_stepping] = l_run
                _tempbuf[_stepping-1] = l_lim
                _stepping = (_stepping+1)%io_no
                for i in range(pulse[0]):
                    if reverse:
                        yield _tempbuf[::-1]
                    else:
                        yield _tempbuf


def wave_list_assign_with_groups(led_no=1, pattern=[], speed=1, groups=None, reverse=False):
    """
    進階函數:支持分組控制不同LED的起始時間
    
    Args:
        led_no: LED數量
        pattern: 波形模式列表
        speed: 速度
        groups: 分組定義,格式為 [(led_indices, start_frame), ...]
                例如: [([0,1,2], 0), ([3,4,5], 20), ([6,7], 40)]
        reverse: 是否反轉
        
    Yields:
        list: LED亮度值列表
    """
    # 初始化起始幀列表
    start_frames = [0] * led_no
    
    if groups:
        for led_indices, start_frame in groups:
            for led_idx in led_indices:
                if led_idx < led_no:
                    start_frames[led_idx] = start_frame
    
    # 調用主函數
    yield from wave_list_assign_with_start_frame(
        led_no=led_no,
        pattern=pattern,
        speed=speed,
        start_frames=start_frames,
        reverse=reverse
    )
        
        
# 0.5ms pulse = (0.5 / 20) * 4095 = 102
# 2.4ms pulse = (2.4 / 20) * 4095 = 491

# for i in range(389):
#     d = 102 +i
#     led_list[0][0].duty(d)
#     time.sleep_ms(10)
    
# for i in range(6226):
#     d = 1638 +i
#     led_list[0].led[0].duty_u16(d)
#     time.sleep_ms(10)
phi0 = 0
phi90 = 1023
phi180 = 2047
phi270 = 3071
phi360 = 4095
eyes_start = [
     {'type': 'keep'    , 'F': 1, 'l_max': 0   , 'l_lim': 0   , 'phi': phi0  , 'end_Time': 60  },
     {'type': 'math_now', 'F': 5, 'l_max': 100 , 'l_lim': 20   , 'phi': phi270, 'end_Time': 100 },
     {'type': 'math_now', 'F': 5, 'l_max': 1023, 'l_lim': 100 , 'phi': phi270, 'end_Time': 200 },
     {'type': 'math_now', 'F': 5, 'l_max': 1023, 'l_lim': 200 , 'phi': phi90 , 'end_Time': 320 },
#      {'type': 'keep'    , 'F': 5, 'l_max': 0 , 'l_lim': 200 , 'phi': phi0  , 'end_Time': 600 },

]

eyes_start1 = [

     {'type': 'math_now', 'F': 10, 'l_max': 500, 'l_lim': 0 , 'phi': phi270 , 'end_Time': 300 },

]

eyes_start2 = [

     {'type': 'math_now', 'F': 20, 'l_max': 500, 'l_lim': 0 , 'phi': phi270 , 'end_Time': 300 },
     {'type': 'keep', 'F': 10, 'l_max': 500, 'l_lim': 0 , 'phi': phi270 , 'end_Time': 310 },

]

rd_io = wave_list_assign_next(64, eyes_start,spacing=10)

rd_io_1 = wave_list_assign_with_start_frame(
    led_no=64,
    pattern=eyes_start,
    speed=1,
    start_frames=range(0, 300, 20)  # 每個LED間隔5幀
)

pulse_list = [(5,5)]
abc = stepping_engine_list_next(led_no=3,pattern= eyes_start2 ,pulse_list=pulse_list)

rd_io = random_flash_pattern_next(64, eyes_start1)
rd_io = wave_list_assign_next(64, eyes_start1, step=10, spacing=20)
rd_io_0 = stepping_wave_next(2, eyes_start1, step=40)
rd_io_1 = stepping_wave_next(22, eyes_start2, step=40)
# for i in rd_io:
#     print(i)


def stepping_engine_next(led_no=1,pattern=[],speed = 1,reverse = False):
    l_max = 0
    l_lim = 4095
    for i in pattern:
        t_l_max = i['l_max']
        t_l_lim = i['l_lim']

        l_max = l_max if t_l_max  < l_max else t_l_max
        l_lim = l_lim if t_l_lim  > l_lim else t_l_lim

    _gen = ledC.mt.is_math_pattern_next(pattern)

    io_no = led_no
    _tempbuf = [0]*(io_no)
#     _stepping = phi%io_no
    _stepping = 0
    while 1 :
        l_run = next(_gen)
        _tempbuf[_stepping] = l_run
        _tempbuf[_stepping-1] = l_lim
        _stepping = (_stepping+1)%io_no
        for i in range(speed):
            if reverse:
                yield _tempbuf[::-1]
            else:
                yield _tempbuf
                
                
def stepping_accelerate_next(led_no=1,pattern=[],speed = 1,reverse = False):
    l_max = 0
    l_lim = 4095
    for i in pattern:
        t_l_max = i['l_max']
        t_l_lim = i['l_lim']

        l_max = l_max if t_l_max  < l_max else t_l_max
        l_lim = l_lim if t_l_lim  > l_lim else t_l_lim
        
    _frame = pattern[-1]['end_Time']

    _gen = ledC.mt.is_math_pattern_next(pattern,stop = True )
    
    # 波形歷史記錄 - 存儲從生成器獲取的所有波形值
    _wave_history = list(_gen)

    io_no = led_no
    _tempbuf = [0]*(io_no)
#     _stepping = phi%io_no
    _stepping = 0
    _target = 1
    while 1 :
        
        for i in range(_frame):

            _stepping = (_stepping+1)%io_no
            _target = io_no if io_no == _target else _target + _target
            
            _tempbuf[_stepping:_target] = _wave_history[_stepping:_target]
            _tempbuf[_stepping-1] = l_lim
        
            for i in range(speed):
                if reverse:
                    yield _tempbuf[::-1]
                else:
                    yield _tempbuf
                
                
                
                


pp = [
    { 'type':'LED','GPIO':only_rgb_io[:2],'_generators': rd_io_0},
    { 'type':'LED','GPIO':only_rgb_io[2:22],'_generators': abc},
    ]


p = [
    {'type': 'keep', 'F': 1, 'l_max': 110, 'l_lim': 0, 'phi': 0, 'end_Time':16}
    ]


    
rd_io_0 = stepping_wave_next(2, eyes_start1, step=40)
diffusion_gen = stepping_engine_next(led_no=8,pattern=p)

def overlay_stepping_engine_list_next(led_no=1, pattern=[], pulse_list=[], overlay=1, gap=1, reverse=False):
    """
    疊加式步進引擎 - 多個引擎錯開啟動
    
    Args:
        led_no: LED數量
        pattern: 亮度模式
        pulse_list: 脈衝列表
        overlay: 疊加引擎數量
        gap: 每個引擎之間的啟動間隔(步數)
        reverse: 是否反向
    
    Yields:
        list: 疊加後的LED亮度值
    """
    gen_list = []
    delay_counters = []  # 每個引擎的延遲計數器
    
    # 創建多個引擎,並設置延遲
    for i in range(overlay):
        gen = stepping_engine_list_next(
            led_no=led_no,
            pattern=pattern,
            pulse_list=pulse_list,  # 這裡應該是 pulse_list,不是 pattern
            reverse=reverse
        )
        gen_list.append(gen)
        delay_counters.append(i * gap)  # 每個引擎延遲 i*gap 步
    
    _tempbuf = [0] * led_no
    step_count = 0
    
    while True:
        # 重置緩衝區
        for i in range(led_no):
            _tempbuf[i] = 0
        
        # 處理每個引擎
        for idx, gen in enumerate(gen_list):
            # 檢查是否到達啟動時間
            if step_count >= delay_counters[idx]:
                _buff = next(gen)
                # 疊加亮度值(取最大值)
                for i in range(led_no):
                    _tempbuf[i] = max(_tempbuf[i], _buff[i])
        
        step_count += 1
        yield _tempbuf
        
        

gen = overlay_stepping_engine_list_next(
    led_no=16,
    pattern=p,
    pulse_list=[(5,1),(3,1),(2,1),(1,5)],
    overlay=5, gap=10,
    reverse=False
)

gen1 = stepping_engine_list_next(
    led_no=16,
    pattern=p,
    pulse_list=[(5,1),(3,1),(2,1),(1,5)],
    reverse=False
)


_list = [
    [only_rgb_io[0],only_rgb_io[24] ],
    [only_rgb_io[1],only_rgb_io[25] ],
    [only_rgb_io[2],only_rgb_io[26] ],
    [only_rgb_io[3],only_rgb_io[27] ],
    [only_rgb_io[4],only_rgb_io[28] ],
    [only_rgb_io[5],only_rgb_io[29] ],
    [only_rgb_io[6],only_rgb_io[30] ],
    [only_rgb_io[7],only_rgb_io[31] ]
    ]


diffusion_init = [
    { 'type':'LED','GPIO':[only_rgb_io[8],only_rgb_io[16]],'_generators': rd_io_0},
#     { 'type':'LED','GPIO':_list,'_generators': diffusion_gen}
    { 'type':'LED','GPIO':only_rgb_io[:8],'_generators': gen1},
    { 'type':'LED','GPIO':only_rgb_io[24:24+8],'_generators': gen}
    ]


ledC.run_Pattern(diffusion_init, run_time = 300*64, debug=1)





        
    

def test_next(in_gen = []):
    while 1 :
        for i in in_gen:
            print(next(i))
        yield
test = test_next(in_gen = [gen])
                
