# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['gui.py'],
             pathex=['/Users/robertbarrett/Documents/eurotrip-planner-master'],
             binaries=[],
             datas=[],
             hiddenimports=['dns','"pymongo[srv]"'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

splash = Splash('splash.jpg',
                binaries=a.binaries,
                datas=a.datas,
                text_pos=(10, 50),
                text_size=12,
                text_color='black')

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='Flight Finder',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='/Users/robertbarrett/Documents/eurotrip-planner-master/Unclebob-Spanish-Travel-Plane.icns')
app = BUNDLE(exe,
             name='Flight Finder.app',
             icon='/Users/robertbarrett/Documents/eurotrip-planner-master/Unclebob-Spanish-Travel-Plane.icns',
             bundle_identifier=None)
