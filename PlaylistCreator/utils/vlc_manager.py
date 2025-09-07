import subprocess
import platform
import vlc

class VLCManager:
    def __init__(self):
        self.vlc_player = None
        
    def play_playlist(self, playlist_path):
        """Riproduce una playlist con VLC"""
        try:
            self.cleanup()
            
            instance = vlc.Instance(["--playlist-autostart", "--interface", "qt"])
            self.vlc_player = instance.media_list_player_new()
            media_list = instance.media_list_new([playlist_path])
            self.vlc_player.set_media_list(media_list)
            self.vlc_player.play()
            
            return True
        except Exception as e:
            print(f"Errore VLC: {e}")
            return False
            
    def cleanup(self):
        """Chiude VLC"""
        if self.vlc_player:
            try:
                self.vlc_player.stop()
                self.vlc_player.release()
            except:
                pass
            finally:
                self.vlc_player = None
        
        self._kill_vlc_process()
        
    def _kill_vlc_process(self):
        """Termina forzatamente il processo VLC"""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["taskkill", "/f", "/im", "vlc.exe"], 
                             capture_output=True, timeout=5)
            else:
                subprocess.run(["pkill", "-f", "vlc"], 
                             capture_output=True, timeout=5)
        except:
            pass

