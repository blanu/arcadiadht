var selfTestAlreadyRun = false;
function selfTest() {
	if (selfTestAlreadyRun) {
		return;
	}
	selfTestAlreadyRun = true;
	if (hash('CC').toUpperCase() != 'D44B1D69E638D37908EE7C9EB212F4FBE465F2B383476C19BB5516E2A365BE1FB33BD8E14B4E03539816B9E1430AEB6B16146E91D03BCE7968A35D7DAA4F9416') {
	    alert('Self test failed; hash CC=' + hash('CC'));
	}
	if (hash('41FB').toUpperCase() != '9FE78BD755A7B4E50E91033C250F65680D83D5288628FC848374496B849E0A2131C538737FC48F017DA892D0F2A61C903790505313C4F22A207FC991E2BEEDC7') {
	    alert('Self test failed; hash 41FB=' + hash('41FB'));
	}
	if (hash('433C5303131624C0021D868A30825475E8D0BD3052A022180398F4CA4423B98214B6BEAAC21C8807A2C33F8C93BD42B092CC1B06CEDF3224D5ED1EC29784444F22E08A55AA58542B524B02CD3D5D5F6907AFE71C5D7462224A3F9D9E53E7E0846DCBB4CE').toUpperCase() 
	        != 'C482F674B5C5CA87BC3417A07053F160C6ED905B6D7A7BBAD4288AEE2854B54C1B7350F6D23BEEDB5C687721FCD1B5E46C19D1625B3AB20EB2C22249C95672C6') {
	    alert('Self test failed; hash len 800');
	}
}
function hex2string(s) { 
    for(var c=[], len=s.length, i=0; i<len; i+=2) 
        c.push(String.fromCharCode(parseInt(s.substring(i, i+2),16))); 
    return c.join(''); 
}
function hex2bytes(s) { 
    for(var c=[], len=s.length, i=0; i<len; i+=2) 
        c.push(parseInt(s.substring(i, i+2),16)); 
    return c; 
}
function string2hex(s) { 
    for(var p=[], len=s.length, i=0; i<len; i++) { 
        p.push((256+s.charCodeAt(i)).toString(16).substring(1)); 
    }
    return p.join(''); 
}
function string2bytes(s) {
    for (var b=[], i=0; i < s.length; i++) b[i] = s.charCodeAt(i);
    return b;
}
function hash(s) {
	selfTest();
    var msg = hex2bytes(s);
    // final: 0x80; first: 0x40; conf: 0x4; msg: 0x30; out: 0x3f
    var tweak = [[0, 32], [(0x80 + 0x40 + 0x4) << 24, 0]], c = [];
    var buff = string2bytes("SHA3\1\0\0\0\0\2");
    block(c, tweak, buff, 0);
    tweak = [[0, 0], [(0x40 + 0x30) << 24, 0]];
    var len = msg.length, pos = 0;
    for(; len > 64; len -= 64, pos += 64) {
        tweak[0][1] += 64;
        block(c, tweak, msg, pos);
        tweak[1][0] = 0x30 << 24;
    }
    tweak[0][1] += len; tweak[1][0] |= 0x80 << 24;
    block(c, tweak, msg, pos);
    tweak[0][1] = 8; tweak[1][0] = (0x80 + 0x40 + 0x3f) << 24;
    block(c, tweak, [], 0);
    for (var hash = [], i = 0; i < 64; i++) {
        var b = shiftRight(c[i >> 3], (i & 7) * 8)[1] & 255;
        hash.push((256+b).toString(16).substring(1)); 
    }
    return hash.join('');
}
function shiftLeft(x, n) {
    if (x == null) return [0, 0];
    if (n > 32) return [x[1] << (n-32), 0];
    if (n == 32) return [x[1], 0];
    if (n == 0) return x;
    return [(x[0] << n) | (x[1] >>> (32 - n)), x[1] << n];
}
function shiftRight(x, n) {
    if (x == null) return [0, 0];
    if (n > 32) return [0, x[0] >>> (n-32)];
    if (n == 32) return [0, x[0]];
    if (n == 0) return x;
    return [x[0] >>> n, (x[0] << (32 - n)) | (x[1] >>> n)];
}
function add(x, y) {
    if (y == null) return x;
    var lsw = (x[1] & 0xffff) + (y[1] & 0xffff);
    var msw = (x[1] >>> 16) + (y[1] >>> 16) + (lsw >>> 16);
    var lowOrder = ((msw & 0xffff) << 16) | (lsw & 0xffff);
    lsw = (x[0] & 0xffff) + (y[0] & 0xffff) + (msw >>>16);
    msw = (x[0] >>> 16)+(y[0] >>> 16) + (lsw >>> 16);
    var highOrder = ((msw & 0xffff) << 16) | (lsw & 0xffff);
    return [highOrder,lowOrder];
}
function xor(a, b) {
    if (b == null) return a;
    return [a[0] ^ b[0], a[1] ^ b[1]];
}
function block(c, tweak, b, off) {
    var R = [46, 36, 19, 37, 33, 42, 14, 27, 17, 49, 36, 39, 44, 56, 54, 9, 
            39, 30, 34, 24, 13, 17, 10, 50, 25, 29, 39, 43, 8, 22, 56, 35];
    var x = [], t = [];
    c[8] = [0x55555555, 0x55555555];
    for (var i = 0; i < 8; i++) {
        for (var j = 7, k = off + i * 8 + 7; j >= 0; j--, k--) {
            t[i] = shiftLeft(t[i], 8);
            t[i][1] |=  b[k] & 255;
        }
        x[i] = add(t[i], c[i]);
        c[8] = xor(c[8], c[i]);
    }
    x[5] = add(x[5], tweak[0]);
    x[6] = add(x[6], tweak[1]);
    tweak[2] = xor(tweak[0], tweak[1]);
    for (var round = 1; round <= 18; round++) {
        var p = 16 - ((round & 1) << 4);
        for (var i = 0; i < 16; i++) {
            // m: 0, 2, 4, 6, 2, 0, 6, 4, 4, 6, 0, 2, 6, 4, 2, 0
            var m = 2 * ((i + (1 + i + i) * (i >> 2)) & 3);
            var n = (1 + i + i) & 7;
            var r = R[p + i];
            x[m] = add(x[m], x[n]);
            x[n] = xor(shiftLeft(x[n], r), shiftRight(x[n], 64 - r));
            x[n] = xor(x[n], x[m]);
            
        }
        for (var i = 0; i < 8; i++) 
            x[i] = add(x[i], c[(round + i) % 9]);
        x[5] = add(x[5], tweak[round % 3]);
        x[6] = add(x[6], tweak[(round + 1) % 3]);
        x[7] = add(x[7], [0, round]);
    }
    for (var i = 0; i < 8; i++) 
        c[i] = xor(t[i], x[i]);
}
