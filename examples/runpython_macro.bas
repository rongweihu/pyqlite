Attribute VB_Name = "PyqliteRunner"
Option Explicit

Sub PricePyqliteActiveSheet()
    RunPython "from pyqlite_xlwings.runpython import price_active_sheet; price_active_sheet()"
End Sub
