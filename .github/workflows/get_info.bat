@echo off
for /f "usebackq" %%i in (`python setup.py -V`) do (
  echo ::set-output name=version::%%i
  goto :done
)
:done
