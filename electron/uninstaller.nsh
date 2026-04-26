; FotoDerp NSIS Uninstaller Script
; Wird von electron-builder fuer Windows-NSIS-Installer eingebunden

!macro customUnInstall
  ; Desktop-Shortcuts entfernen
  Delete "$DESKTOP\FotoDerp.lnk"

  ; Start Menu Eintraege entfernen
  Delete "$STARTMENU\Programs\FotoDerp\FotoDerp.lnk"
  RMDir /r /rebootok "$STARTMENU\Programs\FotoDerp"

  ; App-Daten loeschen (optional, user kann waehlen)
  ; Delete "$APPDATA\FotoDerp\fotoderp.db"
  ; RMDir /r /rebootok "$APPDATA\FotoDerp"

  ; Registry-Eintraege entfernen
  DeleteRegKey HKCU "Software\FotoDerp"
  DeleteRegKey HKLM "Software\FotoDerp"

  ; Dateizuordnungen (optional)
  ; DeleteRegKey HKCR "FotoDerp.Photo"

  MessageBox MB_YESNO|MB_ICONQUESTION \
    "FotoDerp wurde deinstalliert.\n\nApp-Daten (Bilder-Index, Einstellungen) loeschen?" \
    /SD IDYES IDNO NoCleanup

  RMDir /r /rebootok "$APPDATA\FotoDerp"

  NoCleanup:
!macroend
