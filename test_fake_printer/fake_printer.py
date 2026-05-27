#!/usr/bin/env python3
"""
Sahte Termal Yazıcı Simülatörü
===============================

Cashino KP-300/KP-301H termal yazıcıları simüle eden TCP/IP server.
Gerçek yazıcı donanımı olmadan sistemi test etmek için kullanılır.

Özellikler:
- 3 çalışma modu: simple, parse, simulate
- ESC/POS komut parsing
- Status query desteği (DLE EOT)
- Hata simülasyonu (PAPER_OUT, COVER_OPEN, OVERHEAT)
- Port 9100 (RAW printing standart portu)

Kullanım:
    python3 fake_printer.py --mode parse
    python3 fake_printer.py --mode simulate --port 9100
    python3 fake_printer.py --help
"""

import socket
import argparse
import sys
import select
import struct
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from enum import Enum


# ══════════════════════════════════════════════════════════════════════════════
# ESC/POS Komut Sabitleri
# ══════════════════════════════════════════════════════════════════════════════

class ESCPOSCommands:
    """ESC/POS komut tanımları (app/core/escpos_engine.py ile uyumlu)"""
    
    # Kontrol karakterleri
    ESC = 0x1B
    GS = 0x1D
    FS = 0x1C
    DLE = 0x10
    LF = 0x0A
    
    # Temel komutlar
    CMD_INIT = (0x1B, 0x40)  # ESC @
    CMD_LF = (0x0A,)
    
    # Kesme komutları
    CMD_CUT_FULL = (0x1D, 0x56, 0x00)  # GS V 0
    CMD_CUT_PARTIAL = (0x1D, 0x56, 0x01)  # GS V 1
    
    # Metin formatlama
    CMD_BOLD_ON = (0x1B, 0x45, 0x01)  # ESC E 1
    CMD_BOLD_OFF = (0x1B, 0x45, 0x00)  # ESC E 0
    CMD_UNDERLINE_ON = (0x1B, 0x2D, 0x01)  # ESC - 1
    CMD_UNDERLINE_OFF = (0x1B, 0x2D, 0x00)  # ESC - 0
    
    # Hizalama
    CMD_ALIGN_LEFT = (0x1B, 0x61, 0x00)  # ESC a 0
    CMD_ALIGN_CENTER = (0x1B, 0x61, 0x01)  # ESC a 1
    CMD_ALIGN_RIGHT = (0x1B, 0x61, 0x02)  # ESC a 2
    
    # Font boyutu (GS ! n)
    CMD_FONT_NORMAL = (0x1D, 0x21, 0x00)
    CMD_FONT_DOUBLE_HEIGHT = (0x1D, 0x21, 0x10)
    CMD_FONT_DOUBLE_WIDTH = (0x1D, 0x21, 0x01)
    CMD_FONT_DOUBLE = (0x1D, 0x21, 0x11)
    
    # Status query
    CMD_STATUS_QUERY = (0x10, 0x04, 0x01)  # DLE EOT 1
    
    # Görsel komutları
    CMD_RASTER_IMAGE = (0x1D, 0x76, 0x30)  # GS v 0
    
    # QR kod komutları
    CMD_QR_MODEL = (0x1D, 0x28, 0x6B, 0x04, 0x00, 0x31, 0x41, 0x32, 0x00)  # GS ( k - Model 2
    CMD_QR_SIZE = (0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43)  # GS ( k - Size
    CMD_QR_EC = (0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45)  # GS ( k - Error correction
    CMD_QR_STORE = (0x1D, 0x28, 0x6B)  # GS ( k - Store data
    CMD_QR_PRINT = (0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30)  # GS ( k - Print
    
    # Satır besleme
    CMD_FEED_LINES = (0x1B, 0x64)  # ESC d n


# ══════════════════════════════════════════════════════════════════════════════
# Renkli Konsol Çıktısı
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI renk kodları"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Renkler
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    @staticmethod
    def disable():
        """Renkleri devre dışı bırak (log dosyası için)"""
        Colors.RESET = ''
        Colors.BOLD = ''
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.MAGENTA = ''
        Colors.CYAN = ''
        Colors.WHITE = ''
        Colors.GRAY = ''


# ══════════════════════════════════════════════════════════════════════════════
# Status Simülatörü
# ══════════════════════════════════════════════════════════════════════════════

class PrinterError(Enum):
    """Yazıcı hata kodları (app/core/error_handler.py ile uyumlu)"""
    NORMAL = 0x00
    PAPER_OUT = 0x20  # Bit 5
    COVER_OPEN = 0x04  # Bit 2
    OVERHEAT = 0x40  # Bit 6
    PAPER_JAM = 0x20  # Bit 5 (PAPER_OUT ile aynı)


class StatusSimulator:
    """Yazıcı durum simülatörü"""
    
    def __init__(self):
        self.current_error = PrinterError.NORMAL
        self.paper_ok = True
        self.cover_ok = True
        self.temperature_ok = True
    
    def get_status_byte(self) -> int:
        """Mevcut durum byte'ını döndür"""
        return self.current_error.value
    
    def set_error(self, error: PrinterError):
        """Hata simüle et"""
        self.current_error = error
        
        if error == PrinterError.PAPER_OUT or error == PrinterError.PAPER_JAM:
            self.paper_ok = False
        elif error == PrinterError.COVER_OPEN:
            self.cover_ok = False
        elif error == PrinterError.OVERHEAT:
            self.temperature_ok = False
    
    def clear_errors(self):
        """Tüm hataları temizle"""
        self.current_error = PrinterError.NORMAL
        self.paper_ok = True
        self.cover_ok = True
        self.temperature_ok = True
    
    def get_status_text(self) -> str:
        """Durum metnini döndür"""
        paper = f"{Colors.GREEN}✓ OK{Colors.RESET}" if self.paper_ok else f"{Colors.RED}✗ OUT{Colors.RESET}"
        cover = f"{Colors.GREEN}✓ OK{Colors.RESET}" if self.cover_ok else f"{Colors.RED}✗ OPEN{Colors.RESET}"
        temp = f"{Colors.GREEN}✓ OK{Colors.RESET}" if self.temperature_ok else f"{Colors.RED}✗ HOT{Colors.RESET}"
        
        return f"Kağıt: {paper} | Kapak: {cover} | Sıcaklık: {temp}"


# ══════════════════════════════════════════════════════════════════════════════
# ESC/POS Parser
# ══════════════════════════════════════════════════════════════════════════════

class ESCPOSParser:
    """ESC/POS komut parser'ı"""
    
    def __init__(self, encoding: str = 'cp857'):
        self.encoding = encoding
        self.buffer = bytearray()
        self.position = 0
    
    def parse_stream(self, data: bytes) -> List[Dict]:
        """Byte stream'i parse et ve komut listesi döndür"""
        self.buffer.extend(data)
        self.position = 0
        commands = []
        
        while self.position < len(self.buffer):
            cmd = self._parse_next_command()
            if cmd:
                commands.append(cmd)
            else:
                # Tanınmayan byte, text olarak işle
                text_start = self.position
                while self.position < len(self.buffer):
                    b = self.buffer[self.position]
                    # Kontrol karakteri veya ESC/GS/DLE başlangıcı
                    if b in (0x1B, 0x1D, 0x10, 0x0A) or b < 0x20:
                        break
                    self.position += 1
                
                if self.position > text_start:
                    text_bytes = bytes(self.buffer[text_start:self.position])
                    commands.append({
                        'type': 'text',
                        'data': text_bytes,
                        'decoded': self._decode_text(text_bytes)
                    })
        
        # Buffer'ı temizle
        self.buffer.clear()
        return commands
    
    def _parse_next_command(self) -> Optional[Dict]:
        """Bir sonraki komutu parse et"""
        if self.position >= len(self.buffer):
            return None
        
        b = self.buffer[self.position]
        
        # Line feed
        if b == 0x0A:
            self.position += 1
            return {'type': 'lf', 'name': 'Line Feed'}
        
        # ESC komutları
        if b == 0x1B:
            return self._parse_esc_command()
        
        # GS komutları
        if b == 0x1D:
            return self._parse_gs_command()
        
        # DLE komutları (status query)
        if b == 0x10:
            return self._parse_dle_command()
        
        return None
    
    def _parse_esc_command(self) -> Optional[Dict]:
        """ESC komutunu parse et"""
        if self.position + 1 >= len(self.buffer):
            return None
        
        cmd = self.buffer[self.position + 1]
        
        # ESC @ - Initialize
        if cmd == 0x40:
            self.position += 2
            return {'type': 'init', 'name': 'Initialize Printer'}
        
        # ESC E - Bold
        if cmd == 0x45 and self.position + 2 < len(self.buffer):
            value = self.buffer[self.position + 2]
            self.position += 3
            return {'type': 'bold', 'value': bool(value), 'name': f'Bold {"ON" if value else "OFF"}'}
        
        # ESC - - Underline
        if cmd == 0x2D and self.position + 2 < len(self.buffer):
            value = self.buffer[self.position + 2]
            self.position += 3
            return {'type': 'underline', 'value': bool(value), 'name': f'Underline {"ON" if value else "OFF"}'}
        
        # ESC a - Alignment
        if cmd == 0x61 and self.position + 2 < len(self.buffer):
            value = self.buffer[self.position + 2]
            align_map = {0: 'LEFT', 1: 'CENTER', 2: 'RIGHT'}
            self.position += 3
            return {'type': 'align', 'value': value, 'name': f'Align {align_map.get(value, "UNKNOWN")}'}
        
        # ESC d - Feed lines
        if cmd == 0x64 and self.position + 2 < len(self.buffer):
            lines = self.buffer[self.position + 2]
            self.position += 3
            return {'type': 'feed', 'lines': lines, 'name': f'Feed {lines} lines'}
        
        # Tanınmayan ESC komutu
        self.position += 2
        return {'type': 'unknown_esc', 'cmd': cmd, 'name': f'Unknown ESC 0x{cmd:02X}'}
    
    def _parse_gs_command(self) -> Optional[Dict]:
        """GS komutunu parse et"""
        if self.position + 1 >= len(self.buffer):
            return None
        
        cmd = self.buffer[self.position + 1]
        
        # GS ! - Font size
        if cmd == 0x21 and self.position + 2 < len(self.buffer):
            value = self.buffer[self.position + 2]
            font_map = {
                0x00: 'Normal (1x1)',
                0x10: 'Double Height (2x1)',
                0x01: 'Double Width (1x2)',
                0x11: 'Double (2x2)'
            }
            self.position += 3
            return {'type': 'font_size', 'value': value, 'name': f'Font: {font_map.get(value, f"0x{value:02X}")}'}
        
        # GS V - Cut paper
        if cmd == 0x56 and self.position + 2 < len(self.buffer):
            cut_type = self.buffer[self.position + 2]
            cut_map = {0: 'Full Cut', 1: 'Partial Cut'}
            self.position += 3
            return {'type': 'cut', 'cut_type': cut_type, 'name': f'Paper Cut ({cut_map.get(cut_type, "Unknown")})'}
        
        # GS v 0 - Raster bit image
        if cmd == 0x76 and self.position + 2 < len(self.buffer) and self.buffer[self.position + 2] == 0x30:
            if self.position + 7 < len(self.buffer):
                m = self.buffer[self.position + 3]
                xL = self.buffer[self.position + 4]
                xH = self.buffer[self.position + 5]
                yL = self.buffer[self.position + 6]
                yH = self.buffer[self.position + 7]
                
                width_bytes = xL + (xH << 8)
                height = yL + (yH << 8)
                data_size = width_bytes * height
                
                self.position += 8 + data_size
                return {
                    'type': 'image',
                    'width': width_bytes * 8,
                    'height': height,
                    'data_size': data_size,
                    'name': f'Raster Image ({width_bytes * 8}x{height}px, {data_size} bytes)'
                }
        
        # GS ( k - QR code commands
        if cmd == 0x28 and self.position + 2 < len(self.buffer):
            if self.buffer[self.position + 2] == 0x6B:  # 'k'
                return self._parse_qr_command()
        
        # Tanınmayan GS komutu
        self.position += 2
        return {'type': 'unknown_gs', 'cmd': cmd, 'name': f'Unknown GS 0x{cmd:02X}'}
    
    def _parse_qr_command(self) -> Optional[Dict]:
        """QR kod komutunu parse et"""
        if self.position + 5 >= len(self.buffer):
            self.position += 3
            return {'type': 'qr', 'name': 'QR Code (incomplete)'}
        
        pL = self.buffer[self.position + 3]
        pH = self.buffer[self.position + 4]
        cn = self.buffer[self.position + 5]
        fn = self.buffer[self.position + 6]
        
        data_len = pL + (pH << 8)
        
        # Model selection (cn=49 '1', fn=65 'A')
        if cn == 0x31 and fn == 0x41:
            self.position += 3 + data_len + 2
            return {'type': 'qr_model', 'name': 'QR: Set Model 2'}
        
        # Size (cn=49 '1', fn=67 'C')
        if cn == 0x31 and fn == 0x43:
            if self.position + 7 < len(self.buffer):
                size = self.buffer[self.position + 7]
                self.position += 3 + data_len + 2
                return {'type': 'qr_size', 'size': size, 'name': f'QR: Size {size}'}
        
        # Error correction (cn=49 '1', fn=69 'E')
        if cn == 0x31 and fn == 0x45:
            if self.position + 7 < len(self.buffer):
                ec = self.buffer[self.position + 7]
                ec_map = {48: 'L', 49: 'M', 50: 'Q', 51: 'H'}
                self.position += 3 + data_len + 2
                return {'type': 'qr_ec', 'ec': ec, 'name': f'QR: Error Correction {ec_map.get(ec, "?")}'}
        
        # Store data (cn=49 '1', fn=80 'P')
        if cn == 0x31 and fn == 0x50:
            if self.position + 7 + data_len - 3 <= len(self.buffer):
                qr_data = bytes(self.buffer[self.position + 7:self.position + 7 + data_len - 3])
                self.position += 3 + data_len + 2
                try:
                    decoded = qr_data.decode('utf-8')
                    return {'type': 'qr_data', 'data': qr_data, 'decoded': decoded, 'name': f'QR: Data "{decoded}" ({len(qr_data)} bytes)'}
                except:
                    return {'type': 'qr_data', 'data': qr_data, 'name': f'QR: Data ({len(qr_data)} bytes)'}
        
        # Print (cn=49 '1', fn=81 'Q')
        if cn == 0x31 and fn == 0x51:
            self.position += 3 + data_len + 2
            return {'type': 'qr_print', 'name': 'QR: Print'}
        
        # Tanınmayan QR komutu
        self.position += 3 + data_len + 2
        return {'type': 'qr_unknown', 'name': f'QR: Unknown (cn={cn}, fn={fn})'}
    
    def _parse_dle_command(self) -> Optional[Dict]:
        """DLE komutunu parse et (status query)"""
        if self.position + 2 >= len(self.buffer):
            return None
        
        if self.buffer[self.position + 1] == 0x04 and self.buffer[self.position + 2] == 0x01:
            self.position += 3
            return {'type': 'status_query', 'name': 'Status Query (DLE EOT 1)'}
        
        self.position += 2
        return {'type': 'unknown_dle', 'name': 'Unknown DLE command'}
    
    def _decode_text(self, data: bytes) -> str:
        """Metni decode et"""
        try:
            return data.decode(self.encoding)
        except:
            try:
                return data.decode('utf-8')
            except:
                try:
                    return data.decode('latin-1')
                except:
                    return data.hex()


# ══════════════════════════════════════════════════════════════════════════════
# Çıktı Formatı
# ══════════════════════════════════════════════════════════════════════════════

class OutputFormatter:
    """Çıktı formatı yöneticisi"""
    
    @staticmethod
    def format_simple(data: bytes) -> str:
        """Basit mod: hex + ASCII"""
        hex_str = ' '.join(f'{b:02X}' for b in data)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
        
        output = f"{Colors.GRAY}[RECV {len(data)} bytes]{Colors.RESET} {hex_str}\n"
        output += f"{Colors.GRAY}[ASCII]{Colors.RESET} {ascii_str}"
        return output
    
    @staticmethod
    def format_parsed(commands: List[Dict]) -> str:
        """Parse modu: komutları formatla"""
        output = []
        
        for cmd in commands:
            cmd_type = cmd['type']
            
            if cmd_type == 'text':
                text = cmd['decoded']
                output.append(f"{Colors.GREEN}[TEXT]{Colors.RESET} \"{text}\"")
            
            elif cmd_type == 'init':
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC @ - Yazıcı başlatıldı")
            
            elif cmd_type == 'lf':
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} LF - Satır atla")
            
            elif cmd_type == 'bold':
                state = "ON" if cmd['value'] else "OFF"
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC E {1 if cmd['value'] else 0} - Kalın: {state}")
            
            elif cmd_type == 'underline':
                state = "ON" if cmd['value'] else "OFF"
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC - {1 if cmd['value'] else 0} - Altı çizili: {state}")
            
            elif cmd_type == 'align':
                align_map = {0: 'LEFT', 1: 'CENTER', 2: 'RIGHT'}
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC a {cmd['value']} - Hizalama: {align_map.get(cmd['value'], '?')}")
            
            elif cmd_type == 'font_size':
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} GS ! 0x{cmd['value']:02X} - {cmd['name']}")
            
            elif cmd_type == 'cut':
                cut_type = "Full" if cmd['cut_type'] == 0 else "Partial"
                output.append(f"{Colors.MAGENTA}[CUT]{Colors.RESET} GS V {cmd['cut_type']} - Kağıt kes ({cut_type})")
            
            elif cmd_type == 'feed':
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC d {cmd['lines']} - {cmd['lines']} satır besle")
            
            elif cmd_type == 'image':
                output.append(f"{Colors.CYAN}[IMAGE]{Colors.RESET} Raster bit image")
                output.append(f"{Colors.CYAN}[IMAGE]{Colors.RESET} Boyut: {cmd['width']}x{cmd['height']}px ({cmd['data_size']} bytes)")
            
            elif cmd_type.startswith('qr_'):
                if cmd_type == 'qr_model':
                    output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Model ayarlandı: Model 2")
                elif cmd_type == 'qr_size':
                    output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Boyut: {cmd['size']}")
                elif cmd_type == 'qr_ec':
                    output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Hata düzeltme: {cmd['name'].split()[-1]}")
                elif cmd_type == 'qr_data':
                    if 'decoded' in cmd:
                        output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Data: \"{cmd['decoded']}\" ({len(cmd['data'])} bytes)")
                    else:
                        output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Data: {len(cmd['data'])} bytes")
                elif cmd_type == 'qr_print':
                    output.append(f"{Colors.CYAN}[QR]{Colors.RESET} Yazdır komutu")
            
            elif cmd_type == 'status_query':
                output.append(f"{Colors.YELLOW}[STATUS QUERY]{Colors.RESET} DLE EOT 1")
            
            else:
                output.append(f"{Colors.GRAY}[{cmd_type.upper()}]{Colors.RESET} {cmd.get('name', 'Unknown')}")
        
        return '\n'.join(output)
    
    @staticmethod
    def format_simulate(commands: List[Dict], status: StatusSimulator) -> str:
        """Simülasyon modu: gerçekçi çıktı"""
        output = []
        
        for cmd in commands:
            cmd_type = cmd['type']
            
            if cmd_type == 'text':
                text = cmd['decoded']
                output.append(f"{Colors.GREEN}[TEXT]{Colors.RESET} \"{text}\"")
            
            elif cmd_type == 'init':
                output.append(f"{Colors.BLUE}[CMD]{Colors.RESET} ESC @ - Yazıcı başlatıldı")
                output.append(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {status.get_status_text()}")
            
            elif cmd_type == 'cut':
                cut_type = "Full" if cmd['cut_type'] == 0 else "Partial"
                if status.paper_ok:
                    output.append(f"{Colors.GREEN}[CUT]{Colors.RESET} ✓ Kağıt kesildi ({cut_type})")
                else:
                    output.append(f"{Colors.RED}[CUT]{Colors.RESET} ✗ Kağıt yok, kesme başarısız")
            
            elif cmd_type == 'image':
                if status.paper_ok and status.cover_ok:
                    output.append(f"{Colors.GREEN}[PRINT]{Colors.RESET} ✓ Görsel yazdırıldı ({cmd['width']}x{cmd['height']}px)")
                else:
                    output.append(f"{Colors.RED}[PRINT]{Colors.RESET} ✗ Yazdırma başarısız (hata var)")
            
            elif cmd_type == 'qr_print':
                if status.paper_ok and status.cover_ok:
                    output.append(f"{Colors.GREEN}[PRINT]{Colors.RESET} ✓ QR kod yazdırıldı")
                else:
                    output.append(f"{Colors.RED}[PRINT]{Colors.RESET} ✗ QR yazdırma başarısız (hata var)")
            
            elif cmd_type == 'status_query':
                status_byte = status.get_status_byte()
                error_name = "Normal" if status_byte == 0 else f"Error 0x{status_byte:02X}"
                output.append(f"{Colors.YELLOW}[STATUS QUERY]{Colors.RESET} DLE EOT 1")
                output.append(f"{Colors.YELLOW}[RESPONSE]{Colors.RESET} 0x{status_byte:02X} ({error_name})")
        
        return '\n'.join(output)


# ══════════════════════════════════════════════════════════════════════════════
# Sahte Yazıcı Serveri
# ══════════════════════════════════════════════════════════════════════════════

class FakePrinterServer:
    """Sahte termal yazıcı TCP/IP serveri"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 9100, mode: str = 'parse',
                 encoding: str = 'cp857', log_file: Optional[str] = None):
        self.host = host
        self.port = port
        self.mode = mode
        self.encoding = encoding
        self.log_file = log_file
        
        self.parser = ESCPOSParser(encoding)
        self.status = StatusSimulator()
        self.socket = None
        self.running = False
        
        self.stats = {
            'connections': 0,
            'bytes_received': 0,
            'commands_processed': 0,
            'prints': 0,
            'cuts': 0
        }
    
    def start(self):
        """Serveri başlat"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True
            
            self._print_header()
            self._log(f"{Colors.GREEN}🖨️  Sahte Yazıcı başlatıldı!{Colors.RESET}")
            self._log(f"{Colors.CYAN}Port:{Colors.RESET} {self.port}")
            self._log(f"{Colors.CYAN}Mod:{Colors.RESET} {self.mode}")
            self._log(f"{Colors.CYAN}Encoding:{Colors.RESET} {self.encoding}")
            if self.mode == 'simulate':
                self._log(f"\n{Colors.YELLOW}Hata simülasyonu tuşları:{Colors.RESET}")
                self._log(f"  {Colors.BOLD}[P]{Colors.RESET} Paper Out  {Colors.BOLD}[C]{Colors.RESET} Cover Open  {Colors.BOLD}[H]{Colors.RESET} Overheat  {Colors.BOLD}[J]{Colors.RESET} Paper Jam  {Colors.BOLD}[R]{Colors.RESET} Reset")
            self._log(f"{Colors.GRAY}Kapatmak için CTRL+C{Colors.RESET}")
            self._log("─" * 70)
            
            while self.running:
                try:
                    # Simulate modunda klavye girişini kontrol et
                    if self.mode == 'simulate':
                        self._check_keyboard_input()
                    
                    # Bağlantı bekle (timeout ile)
                    self.socket.settimeout(0.5)
                    try:
                        conn, addr = self.socket.accept()
                        self._handle_client(conn, addr)
                    except socket.timeout:
                        continue
                
                except KeyboardInterrupt:
                    break
        
        except OSError as e:
            if e.errno == 48:  # Address already in use
                self._log(f"{Colors.RED}✗ Hata: Port {self.port} zaten kullanımda!{Colors.RESET}")
                self._log(f"{Colors.YELLOW}Başka bir port deneyin: --port 9101{Colors.RESET}")
            else:
                self._log(f"{Colors.RED}✗ Hata: {e}{Colors.RESET}")
        
        finally:
            self.stop()
    
    def stop(self):
        """Serveri durdur"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        self._log("\n" + "─" * 70)
        self._log(f"{Colors.YELLOW}📊 İstatistikler:{Colors.RESET}")
        self._log(f"  Toplam bağlantı: {self.stats['connections']}")
        self._log(f"  Toplam byte alındı: {self.stats['bytes_received']:,}")
        self._log(f"  Toplam komut: {self.stats['commands_processed']}")
        self._log(f"  Yazdırma işlemi: {self.stats['prints']}")
        self._log(f"  Kesme işlemi: {self.stats['cuts']}")
        self._log(f"\n{Colors.GREEN}Sahte yazıcı kapatıldı.{Colors.RESET}")
    
    def _handle_client(self, conn: socket.socket, addr: Tuple):
        """Client bağlantısını yönet"""
        self.stats['connections'] += 1
        
        self._log(f"\n{Colors.GREEN}[+] Bağlantı:{Colors.RESET} {addr[0]}:{addr[1]}")
        
        if self.mode == 'simulate':
            self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}")
        
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                
                self.stats['bytes_received'] += len(data)
                
                # Basit mod: sadece hex göster
                if self.mode == 'simple':
                    output = OutputFormatter.format_simple(data)
                    self._log(output)
                
                # Parse veya simulate modu
                else:
                    commands = self.parser.parse_stream(data)
                    self.stats['commands_processed'] += len(commands)
                    
                    # İstatistikleri güncelle
                    for cmd in commands:
                        if cmd['type'] == 'cut':
                            self.stats['cuts'] += 1
                        elif cmd['type'] in ('image', 'qr_print'):
                            self.stats['prints'] += 1
                    
                    # Status query'ye yanıt ver
                    for cmd in commands:
                        if cmd['type'] == 'status_query':
                            status_byte = bytes([self.status.get_status_byte()])
                            conn.send(status_byte)
                    
                    # Çıktıyı formatla
                    if self.mode == 'parse':
                        output = OutputFormatter.format_parsed(commands)
                    else:  # simulate
                        output = OutputFormatter.format_simulate(commands, self.status)
                    
                    if output:
                        self._log(output)
        
        except Exception as e:
            self._log(f"{Colors.RED}[!] Hata: {e}{Colors.RESET}")
        
        finally:
            conn.close()
            self._log(f"{Colors.GRAY}[-] Bağlantı kapatıldı: {addr[0]}:{addr[1]}{Colors.RESET}")
    
    def _check_keyboard_input(self):
        """Klavye girişini kontrol et (simulate modu için)"""
        # Non-blocking stdin okuma
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1).lower()
            
            if key == 'p':
                self.status.set_error(PrinterError.PAPER_OUT)
                self._log(f"\n{Colors.RED}[!] HATA SİMÜLE EDİLDİ: PAPER_OUT{Colors.RESET}")
                self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}\n")
            
            elif key == 'c':
                self.status.set_error(PrinterError.COVER_OPEN)
                self._log(f"\n{Colors.RED}[!] HATA SİMÜLE EDİLDİ: COVER_OPEN{Colors.RESET}")
                self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}\n")
            
            elif key == 'h':
                self.status.set_error(PrinterError.OVERHEAT)
                self._log(f"\n{Colors.RED}[!] HATA SİMÜLE EDİLDİ: OVERHEAT{Colors.RESET}")
                self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}\n")
            
            elif key == 'j':
                self.status.set_error(PrinterError.PAPER_JAM)
                self._log(f"\n{Colors.RED}[!] HATA SİMÜLE EDİLDİ: PAPER_JAM{Colors.RESET}")
                self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}\n")
            
            elif key == 'r':
                self.status.clear_errors()
                self._log(f"\n{Colors.GREEN}[✓] Tüm hatalar temizlendi{Colors.RESET}")
                self._log(f"{Colors.YELLOW}[STATUS]{Colors.RESET} {self.status.get_status_text()}\n")
    
    def _print_header(self):
        """Başlık yazdır"""
        header = f"""
{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║           Sahte Termal Yazıcı Simülatörü v1.0                    ║
║           Cashino KP-300 / KP-301H Compatible                     ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
        print(header)
    
    def _log(self, message: str):
        """Mesajı konsola ve log dosyasına yaz"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Konsola yaz
        print(message)

        # Log dosyasına yaz (renk kodları olmadan)
        if self.log_file:
            # ANSI renk kodlarını temizle
            import re
            clean_message = re.sub(r'\033\[[0-9;]+m', '', message)

            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    # Her satırı ayrı ayrı timestamp ile yaz
                    for line in clean_message.split('\n'):
                        if line.strip():
                            f.write(f"[{timestamp}] {line}\n")
                        else:
                            f.write('\n')
            except Exception as e:
                print(f"{Colors.RED}Log yazma hatası: {e}{Colors.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# Ana Program
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Ana program"""
    parser = argparse.ArgumentParser(
        description='Sahte Termal Yazıcı Simülatörü - Cashino KP-300/KP-301H uyumlu',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Çalışma Modları:
  simple    - Gelen byte'ları hex ve ASCII formatında göster (hızlı test)
  parse     - ESC/POS komutlarını parse et ve anlamlı göster (varsayılan)
  simulate  - Gerçek yazıcı gibi davran, status query'lere yanıt ver, hata simüle et

Kullanım Örnekleri:
  %(prog)s --mode simple
  %(prog)s --mode parse --port 9100
  %(prog)s --mode simulate --log printer.log
  %(prog)s --mode parse --encoding utf-8

Hata Simülasyonu (simulate modunda):
  [P] Paper Out    - Kağıt bitti
  [C] Cover Open   - Kapak açık
  [H] Overheat     - Aşırı ısınma
  [J] Paper Jam    - Kağıt sıkışması
  [R] Reset        - Tüm hataları temizle

Test Etmek İçin:
  1. Terminal 1: python3 fake_printer.py --mode parse
  2. Terminal 2: echo "Test" | nc localhost 9100
  
  veya API ile:
  1. .env dosyasında: LAN_HOST=127.0.0.1, LAN_PORT=9100
  2. python3 fake_printer.py --mode parse
  3. curl -X POST http://localhost:8000/print/text ...
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['simple', 'parse', 'simulate'],
        default='parse',
        help='Çalışma modu (varsayılan: parse)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Dinlenecek IP adresi (varsayılan: 0.0.0.0 - tüm IP\'ler)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=9100,
        help='Dinlenecek port (varsayılan: 9100)'
    )
    
    parser.add_argument(
        '--encoding',
        choices=['cp857', 'utf-8', 'latin-1'],
        default='cp857',
        help='Metin encoding (varsayılan: cp857 - Türkçe)'
    )
    
    parser.add_argument(
        '--log',
        metavar='FILE',
        help='Log dosyası (opsiyonel)'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Renkli çıktıyı devre dışı bırak'
    )
    
    args = parser.parse_args()
    
    # Renkleri devre dışı bırak
    if args.no_color:
        Colors.disable()
    
    # Simulate modunda stdin'i non-blocking yap
    if args.mode == 'simulate':
        import termios
        import tty
        
        # Terminal ayarlarını kaydet
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            # Serveri başlat
            server = FakePrinterServer(
                host=args.host,
                port=args.port,
                mode=args.mode,
                encoding=args.encoding,
                log_file=args.log
            )
            server.start()
        
        finally:
            # Terminal ayarlarını geri yükle
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    else:
        # Normal mod
        server = FakePrinterServer(
            host=args.host,
            port=args.port,
            mode=args.mode,
            encoding=args.encoding,
            log_file=args.log
        )
        server.start()


if __name__ == '__main__':
    main()
