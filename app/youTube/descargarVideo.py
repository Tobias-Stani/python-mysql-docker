import yt_dlp
import pyfiglet
import shutil
import sys
import os
import platform
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

class VideoDownloader:
    def __init__(self):
        self.console = Console()
        self._crear_carpeta_descargas()
        self._mostrar_titulo()

    def _crear_carpeta_descargas(self):
        """Crea la carpeta 'Descargas' si no existe."""
        if not os.path.exists("Descargas"):
            os.makedirs("Descargas")

    def _mostrar_titulo(self):
        """Muestra el título en ASCII solo una vez al iniciar."""
        ancho_terminal = shutil.get_terminal_size().columns
        fuente = "small" if ancho_terminal < 50 else "standard" if ancho_terminal < 80 else "big"
        titulo = pyfiglet.figlet_format("Descarga de Videos", font=fuente)
        self.console.print(Panel(titulo, title="🎬 YouTube | Twitter | X", style="bold cyan", width=ancho_terminal - 2))

    def _limpiar_pantalla(self):
        """Limpia la pantalla de la consola según el sistema operativo."""
        sistema = platform.system()
        if sistema == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    def _seleccionar_formato(self):
        """Muestra opciones para descargar video con audio o solo audio."""
        table = Table(title="🎵 Formato de descarga")
        table.add_column("Opción", style="bold cyan")
        table.add_column("Formato", style="bold yellow")
        table.add_row("1", "📹 Video con audio")
        table.add_row("2", "🎧 Solo audio")
        self.console.print(table)
        return Prompt.ask("[bold yellow]Elige una opción[/]", choices=["1", "2"])

    def _progreso(self, d):
        """Actualiza la barra de progreso."""
        if d['status'] == 'downloading':
            descargado = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 100)
            self.progress.update(self.task_id, completed=descargado, total=total)
        elif d['status'] == 'finished':
            self.progress.stop()
            self.console.print("\n✅ [bold green]Descarga exitosa[/] 🎉")

    def descargar_video(self, url, opcion):
        """Descarga el video o audio según la opción elegida."""
        format_string = "bestaudio/best" if opcion == "2" else "best"

        opciones = {
            'format': format_string,
            'progress_hooks': [self._progreso],
            'quiet': True,
            'noprogress': True,
            'logtostderr': False,
            'cookies': 'cookies.txt',
            'outtmpl': "Descargas/%(title)s.%(ext)s",  # Guarda en la carpeta 'Descargas'
            'postprocessors': [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}] if opcion == "2" else []
        }

        with Progress() as self.progress:
            self.task_id = self.progress.add_task("[cyan]⬇ Descargando...", total=100)
            try:
                with yt_dlp.YoutubeDL(opciones) as ydl:
                    ydl.download([url])
            except Exception:
                self.progress.stop()
                self.console.print("\n❌ [bold red]No se pudo descargar el video[/]", style="bold red")

def main():
    downloader = VideoDownloader()

    while True:
        # Solicitar el link del video
        url = Prompt.ask("\n[bold yellow]🔗 Ingresa el enlace del video (o escribe 'salir' para cerrar)[/]")
        
        if url.lower() == "salir":
            print("\n👋 [bold cyan]Gracias por usar el descargador de videos![/]")
            sys.exit(0)  # Termina el programa

        # Elegir formato
        opcion = downloader._seleccionar_formato()

        # Descargar el video
        downloader.descargar_video(url, opcion)

        # Esperar antes de limpiar la pantalla
        Prompt.ask("\n[bold cyan]Presiona Enter para continuar...[/]")

        # Limpiar la pantalla antes de la siguiente descarga
        downloader._limpiar_pantalla()

if __name__ == "__main__":
    main()
