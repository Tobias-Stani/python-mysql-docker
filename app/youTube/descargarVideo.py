import yt_dlp
import pyfiglet
import shutil
import sys
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt
from rich.panel import Panel

class VideoDownloader:
    def __init__(self):
        self.console = Console()
        self._mostrar_titulo()
        self.url = Prompt.ask("[bold yellow]🔗 Ingresa el enlace del video[/]")
    
    def _mostrar_titulo(self):
        ancho_terminal = shutil.get_terminal_size().columns
        fuente = "small" if ancho_terminal < 50 else "standard" if ancho_terminal < 80 else "big"
        titulo = pyfiglet.figlet_format("Descarga de Videos", font=fuente)
        self.console.print(Panel(titulo, title="🎬 YouTube | Twitter | X", style="bold cyan", width=ancho_terminal - 2))
    
    def _progreso(self, d):
        if d['status'] == 'downloading':
            descargado = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 100)
            self.progress.update(self.task_id, completed=descargado, total=total)
        elif d['status'] == 'finished':
            self.progress.stop()
            self.console.print("\n✅ [bold green]Descarga exitosa[/] 🎉")
    
    def descargar_video(self):
        opciones = {
            'format': 'best',
            'progress_hooks': [self._progreso],
            'quiet': True,
            'noprogress': True,
            'logtostderr': False,
            'cookies': 'cookies.txt' 
        }
        
        with Progress() as self.progress:
            self.task_id = self.progress.add_task("[cyan]⬇ Descargando...", total=100)
            try:
                with yt_dlp.YoutubeDL(opciones) as ydl:
                    ydl.download([self.url])
            except Exception:
                self.progress.stop()
                self.console.print("\n❌ [bold red]No se pudo descargar el video[/]", style="bold red")
                sys.exit(1)

if __name__ == "__main__":
    downloader = VideoDownloader()
    downloader.descargar_video()
