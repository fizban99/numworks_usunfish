const = lambda x: x 
import os
os.environ['KANDINSKY_OS_MODE'] = '0'
os.environ['KANDINSKY_ZOOM_RATIO'] = "3"
try:
    import usunfish_engine as u
except:
    assert False, '\nusunfish_engine.py missing'
from kandinsky import fill_rect as fr,draw_string as ds
from ion import *
from ion import keydown as kd
from time import sleep as slp



pc_colors = (65535,0, 63422, 52889,65535,0, 38066, 50646)

bg=(59225, 31883)
tcol=(59225, 38066)

pcs = ('DhLA3AweHIHmGIHmGIHmGIHmGMHhyB5hhB7hRJ6UweHMHhyBPiGEE+oUAT7iEBPuoRPuod3V',
       'EhXEHMjAEhzEwanIweZcCBYeYcgSXqGEHu4UQe7hQB7uYQHmXqEOJUHmEBZYHqEAXB7hDEHuIQwB7iFMHuYUzd1IH/8QQe7mFB7uYU3d0A==',
       'DxbA3ExWXAweHAxWHEwBIcjBYUHIGhASGEGhQWFEGhAaFAHhAeEAHhAeEAHp4QAe6hAB7qEAHuoQQe4hSB6hhN2UAf+xAe7iEe7iHd2Q',
       'ExXMzIzMyImFiUgWEBYQFhSBaWlhSB7uFIHu4Uwe5hjAHuHMAe4cwB7hzAHuHMAe4cwB7hzAHuHMAe4czd2IH/8UQe7mEEHu5hBN3dA=',
       'FhXEnJxMAaFBocDAGhQaHAwBoUVhwAlBIcEhSQGhAWFBYQGhGhAWFBYQGhFhQWFBYUFhAWEBYUFhAWEEFlpaVhRBoe4aFIHu5hiB7uYYwe7hzB7uHMAe5hwMDd3Awf/xyB7uYYge7mGI3d2A',
       'FhbMDcwMwBYcwMheXIyB5hyMheXIzB4cyNXtWEHu7hQB7u5hAenmnhGhgeGBoRoYHhgaEBoUHhQaEAHhAeEB4QQeHmHhSB7uYYwe7hzA3dwMH/8cge7mGIHu5hiN3dg=',
)  

font = (15329376,7968529,6887776,15310472,14809440,2257452,261003744,10065681,7479858,15820950,6915222,4519268,6915871,6919958,2237583,6919830)


_HIGHLIGHT = const(11615)

def rgb(c): return ((c>>11&0x1F)*255//31, (c>>5&0x3F)*255//63, (c&0x1F)*255//31)


def font_gen(n):
    for i in range(0,28):
        yield 1, (1-(font[n]>>i)&1)*65535

def gcl(data, colors, off):
    yield from  (((nibble>>2)+1,colors[(nibble&3)+off]) for byte in data for nibble in [(byte >> 4), byte & 0x0F])

def dr_ln(x, y, lx, ly, c):
    if c != (255, 255, 255):
        fr(x, y, lx, ly, c)

def dr_img(w, h, x, y,gdc):
    x0, y0, pc, tl = x, y, -1, 0
    while True:
        l, c =next(gdc)
        c = rgb(c)
        if x + l > x0 + w :
            if tl > 0:
                dr_ln(x - tl, y, tl, 1, pc)
            y, x, pc, tl = y+1 , x0, c, 0
        if pc != c:
            if pc != -1 and tl > 0:
                dr_ln(x - tl, y, tl, 1, pc)
            pc, tl = c, l
        else:
            tl += l
        x += l
        if x == x0 + w and y ==y0 + h-1:
            break
    dr_ln(x - tl, y, tl, 1, pc)

def dr_sq(x, y):
    fr(x*26+11, y*26+1, 26, 26, rgb(bg[(x%2)^(y%2)]))

def draw_board():
    i=1
    fr(0,0,222,222,(255,255,255))
    fr(10,0,210,210,(0,0,0))
    fr(11,1,208,208,rgb(bg[0]))
    for x in range (8):
        for y in range (i,8,2):
            dr_sq(x,y)
        i = 1-i

def cur(c, x,y):
    fr(x,y,24,2,c)
    fr(x,y+24,24,2,c)
    fr(x,y,2,24,c)
    fr(x+24,y,2,26,c)  

def dr_cur(sq, c=None):
    # get coordinates of the cursor
    y, x = divmod(sq, 8)
    if c is None:
        # default background color to the square color
        c = bg[(x%2)^(y%2)]
    cur(rgb(c), x*26+11,y*26+1)


def move_cur(v):
    global cind, gm
    if not gm: return
    dr_cur(gm[cind], _HIGHLIGHT)
    if abs(v) == 1:
        # move the cursor to the next position
        cind = (cind + v) % len(gm)
    else:
        match = False
        sq = gm[cind]
        while not match:
            sq +=v
            y = sq//8
            
            # find the closest square in the upper or lower row
            isq = -1
            for isq in (sq for sq in sorted(gm) if sq//8 == y):
                if isq == sq:
                    cind = gm.index(isq)
                    match = True
                    break 
                elif isq!=-1 and isq > sq:
                    match = True
                    cind = gm.index(isq)
                    break
            if not match:
                if isq != -1:
                    cind = gm.index(isq)
                    match = True
                else:
                    if sq+v>63 or sq+v<0:
                        match = True
            
    dr_cur(gm[cind], 0)


def dr_high(on):
    global cind, gm
    for cind in range(len(gm)):
        if on:
            dr_cur(gm[cind],_HIGHLIGHT)
        else:
            dr_cur(gm[cind])

def g_gm1():
    global gm
    gm = list(set((m&0x3FFF)>>8 for m in u.gen_moves() if not u.can_kill_king(m&0x3FFF)))
    gm.sort()


def set_initial_sq(i = 0):
    global gm, cind, origin

    origin = True
    g_gm1()
    dr_high(True)
    if len(gm)>i:
        cind = i
    else:
        cind = 0
    if len(gm)==0 and u.can_kill_king(0):
        ds("Checkmate!",225,20)
        return
    elif len(gm)==0:
        ds("Stalemate!",225,20)
        return
    dr_cur(gm[cind], 0)
    
def dr_pc(x,y,p):
    piece = pcs[p&7]
    data = u.fb64(piece)
    w, h = next(data), next(data)       
    y = y * 26 + 26-h-1
    x = x * 26 + (24 - w) // 2  +12 
    dr_img(w, h, x,y,gcl(data,pc_colors,(p>>3)*4))


def dr_mv(o,d,p):
    if p|8 ==13 and abs(o-d) == 2:
        # calculate the actual o and d squares
        # the board does not match the visual
        # if it's black turn and not inverted
        # or white turn and inverted
        if (u.g_trn() == 1 and not invert) or (u.g_trn() == 0 and invert):
            d2 = 63 - d
            inv = -1
        else:
            d2 = d
            inv = 1
        # castling
        r,c = divmod(d,8)
        for i in  range(-2,3):
            if 0 <= c+i < 8:
                if 0<c+i <8:
                    dr_sq(c+i,r)
                    rk = u.board[d2+i*inv]
                    if rk|8 != 14:
                        # if it is white turn, the color is black
                        if u.g_trn() == 0:
                            rk = rk|0x08
                        else:
                            rk = rk&0x07
                        dr_pc(c+i,r,rk)
    else:
        dr_sq(o&7,o>>3)
        dr_sq(d&7,d>>3)
        dr_pc(d&7,d>>3,p)

def is_end_game():
    global gm

    if u.can_kill_king(0, ccheck=False):
        g_gm1()
        if not gm:
            ds("Checkmate!",220,18)
            return True
        else:
            ds("  Check!",220,18)
    else:
        g_gm1()
        if not gm:
            ds("Stalemate",220,18)
            return True
    if u.threefold():
        ds("Draw-rep",220,18)
        gm = []
        return True


def dr_trn(trn, ply):
    if ply%2 == 0:
        ds(str(ply//2),220,0)
    fr(234, 2, 13, 13, rgb(tcol[trn]))

def upd_moves(mv):
    global prev_movs, undo, trn


    if mv!=0:
        undo.append(u.pscore)
        undo.append(u.wc_bc_ep_kp)
        undo.append(u.last_mv<<16|u.op_mode<<15|u.op_ind)
        dif = u.mk_mv(mv)
        trn = u.g_trn()
        undo.append(dif)
        undo = undo[-8:]
        w_mv = u.render_mv(mv, 1-trn)
        prev_movs = mv.to_bytes(2,"big") + prev_movs[:6]
    else:
        trn = u.g_trn()
    fr(224, 2, 13, 13, rgb(tcol[trn]))
    ds("          ",240,0)
    ds("          ",220,20)


    for i in range(0, 8, 2):
        if i < len(prev_movs):        
            w_mv = u.render_mv(int.from_bytes(prev_movs[i:i+2], "big"), (1+trn+i//2)%2)
            if (u.ply-(i//2))%2 != 0:
                ds(str((u.ply-(i//2))//2+1)+ ".",222,38+i*10)
            else:
                ds("          ",220,38+i*10)
            fr(250, 40+i*10, 13, 13, rgb(tcol[(1+trn+i//2)%2]))
            ds(w_mv,265,38+i*10)
        else:
            ds("          ",220,38+i*10)


def think():
    global gm, trn
    ds("Thinking",240,0)
    gm = [m&0x3FFF for m in u.gen_moves() if not u.can_kill_king(m&0x3FFF)]
    best=0
    for _depth, gamma, score, mv in u.search():
        if score >= gamma:   
            best = mv  
        if u.nodes > 125*(2**lvl):
            if best==0:
                best = mv
            if best in gm:
                gm = None
                break
            elif lvl == 0:
                if len(gm) > 0:
                    best = gm[-1]
                    break
                else:
                    best = 0
                    break
            elif _depth > 1:
                best = 0
                break

    ds("#Nod:" + ((str(u.nodes)+"  ") if u.nodes>0 else ("opng")),222,125) 
    
    isqb = 0
    dsqb = 0
    if best !=0:
        dsqb = best&0x3F
        isqb = best>>8        
        # computer is always at the top
        # we have to invert the indexes of the move
        # because who moves is always at the bottom
        dsqb = (63 - dsqb) 
        isqb = (63 - isqb)
        upd_moves(best) 
        if trn == 1:
            # if it is now black turn, black is at the bottom (turned to white).
            # white is at the top turned to black  
            # since white moved, the piece at the top has wrong color
            p = u.board[dsqb]^0x08
        else:
            # if it is now white turn, white is at the bottom (as white).
            # black is at the top (as black)
            # since black moved, the piece has the right color
            p = u.board[dsqb]
        dr_mv(isqb,dsqb,p)
        dr_cur(isqb, 65348)
        dr_cur(dsqb, 65348)
        if not is_end_game():
            set_initial_sq(0)
        u.upd_hist()
    else:
        ds("Resign",220,18)
        gm=[]
    return isqb, dsqb 

def draw_pcs():
    r = 0
    c = 0
    if invert: 
        u.board.reverse()
        if u.g_trn()==1:
            # white is displayed on top in inverted mode,
            # the board needs to be reversed only if it is white turn
            # if its black turn, the board has the wrong colors
            # change colors and undo the rotation
            u.reverse()
    elif u.g_trn()==1:
        u.reverse()

    for p in u.board:
        if p&7 < 6:
            dr_pc(c,r,p)
        c = c+1 if c < 7 else 0
        if c == 0:
            y = r * 26 + 18
            fnt = 8+r if invert else 15-r 
            dr_img(4, 7, 3,y,font_gen(fnt))
            r = r+1         
    for i in range(8):
        x = i * 26 + 20
        fnt = 7-i if invert  else i 
        dr_img(4, 7, x,212,font_gen(fnt))
    if invert:
        u.board.reverse()
        if u.g_trn()==1:
            u.reverse()
    elif u.g_trn()==1:
        u.reverse()
 
def dr_lvl(lvl):
    ds("[Ln] Lvl " + str(lvl),220,195)

invert = False 
draw_board()

cind = 0

draw_pcs()

keys =         '\x00\x03\x01\x02\x13\x1B\x04\x11'
key_pressing = '\x00\x00\x00\x00\x00\x00\x00\x00'
prev_movs = b""
undo = []
lvl = 0
ds("[Bk] Undo" ,220,155)
ds("["+chr(960)+"]  Rot" ,220,175)
dr_lvl(lvl)
set_initial_sq(4)
trn = 0
upd_moves(0)
# squares of the last opponent move
dsqb = -1
isqb = -1
while True:
    for ik, k in enumerate(keys):
        k = ord(k)
        if kd(k):
            if  not ord(key_pressing[ik]):
                key_pressing= key_pressing[:ik] + '\x01' + key_pressing[ik+1:]
                if k==KEY_LEFT: move_cur(-1)
                elif k==KEY_RIGHT: move_cur(1)
                elif k==KEY_UP: move_cur(-8)
                elif k==KEY_DOWN: move_cur(8) 
                elif k==KEY_BACKSPACE:
                    if len(undo)>7:
                        for i in range(2):
                            u.reverse()
                            u.restore(int.from_bytes(prev_movs[i*2:i*2+2], "big"),undo.pop())
                            v = undo.pop()
                            u.last_mv = v>>16
                            u.op_ind = v&0x3FFF
                            u.op_mode = (v>>15)&0x01
                            u.wc_bc_ep_kp = undo.pop()
                            u.pscore = undo.pop()
                            u.ply -= 1
                            # check if the move was half move (undo and end of game)
                            if i==0 and trn == u.g_trn():
                                break

                        prev_movs = prev_movs[4:]
                        draw_board()
                        draw_pcs()
                        upd_moves(0)
                        u.history = u.history[:-2]
                        set_initial_sq(0)
                elif k==KEY_LN:
                    lvl = (lvl + 1) % 7
                    dr_lvl(lvl)
                elif k==KEY_PI:
                    if not is_end_game():
                        draw_board()
                        invert = not invert
                        draw_pcs()           
                        isqb, dsqb = think()

                elif k==KEY_EXE or k==KEY_OK:
                    if origin:
                        # first part of the move
                        ds(u.render(gm[cind]),245,0)
                        origin = False
                        # store initial index and square
                        iind = cind
                        isq = gm[cind]
                        dr_high(False)
                        gm = list(set(m&0x3F for m in u.gen_moves() if  ((m&0x3FFF)>>8 == isq ) and not u.can_kill_king(m&0x3FFF)))                        
                        gm.append(isq)
                        gm.sort()
                        dr_high(True)
                        cind = gm.index(isq)
                        dr_cur(isq, 0)
                    else:
                        # second part of the move
                        origin = True

                        # store final index 
                        dind = cind
                        dr_high(False)

                        if dind == gm.index(isq):
                            # cancel move
                            set_initial_sq(iind)
                            ds("     ",225,40)
                        else:
                            # remove cursor of opponent move
                            if isqb != -1:
                                dr_cur(isqb)
                                dr_cur(dsqb)
                            mv = (isq<<8)| gm[dind]
                            trn = 1-u.g_trn()
                            w_mv = None
                            dsq = gm[dind]
                            mv = isq<<8| dsq|0xC0  # assume queen promotion
                            # if it is white turn, the board is correct
                            upd_moves(mv)                            
                            if u.g_trn() == 0:
                                # we were black
                                p = u.board[63-dsq]
                            else:
                                p = u.board[63-dsq]^0x08
                            # human is always at the bottom
                            # so the move indexes are always correct
                            dr_mv(isq, dsq, p)
                            u.upd_hist()
                            if not is_end_game():
                                isqb, dsqb = think()
                            else:
                                # if it is end game, undo should only allow
                                # a half move
                                trn = u.g_trn()^1

        else:
            key_pressing=key_pressing[:ik] + '\x00' + key_pressing[ik+1:]


    slp(0.05)