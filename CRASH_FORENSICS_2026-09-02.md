# Crash forensics — 2026-09-02

Box: i7-2600K, ASUS P8P67 PRO rev 3.1, BIOS 3602 (2012), 2x8GB Kingston HX321C11SR/8 @1333 (DRAM 1.55V, VCCIO 1.10V), NVIDIA Quadro P2000 (driver 32.0.15.8216).

## The 02-Sep event was a hang, not a BSOD

| Time (local) | Event |
|---|---|
| 09:29 | boot |
| 09:55:26 | ingest starts (4 files, TM1 Theorie-027-051 first) |
| 10:32:37-38 | `disk` 153 x2, IO retried, Disk 2 = F: — same minute `vdb_entities.json` was written |
| 11:44:44 | `0xc0000005` storm begins: WindowsTerminal, TextInputHost, Explorer, dwm |
| 11:44:47 | Winlogon 1002 "shell stopped unexpectedly", restarts userinit.exe — 38 times |
| 11:44-11:52 | 2019 dwm.exe + 25 Explorer.EXE crashes, ALL `0xc0000005` in `dcomp.dll`; DWM restart counter reaches 185 |
| 11:52:35 | power button pressed (decoded from event 41 `PowerButtonTimestamp`) |
| 11:53:07 | boot. Event 41 `BugcheckCode=0`, `LongPowerButtonPressDetected=false` |

No bugcheck, no dump, no event 1001. `AutoReboot=0`, so a real BSOD would have stayed on screen. The kernel survived; the user session died and the box was power-cycled.

Signature: the same module faulting identically across 6+ unrelated processes, 2000 times, clearing only on reboot = a corrupted memory-resident cached code page. Disk faults self-heal on re-read; GPU faults log TDR event 4101 — there were none, and no WHEA and no nvlddmkm events.

## Five minidumps, all kernel memory management

| Date | Bugcheck | Failure bucket | Victim process |
|---|---|---|---|
| 20-Aug | 0x7E | AV_nt!RtlDeleteNoSplay (VAD tree, via FLTMGR) | System |
| 25-Aug | 0x1E | AV_nt!KiDispatchException -> GP fault | csrss.exe |
| 27-Aug 19:21 | 0x139 | CORRUPT_LIST_ENTRY bam!BampThrottlingWorker | System |
| 27-Aug 20:10 | 0x1A_41792 | nt!MiDeleteVa — "a corrupt PTE has been detected", Arg3 `00a5000000000000` | AnVir.exe |
| 29-Aug | 0x4E_99 | nt!MiBadShareCount — "a PTE or PFN is corrupt" | python.exe (the ingest) |

Read with:
```
$env:_NT_SYMBOL_PATH='srv*C:\symbols*https://msdl.microsoft.com/download/symbols'
& 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe' -z <dump> -y $env:_NT_SYMBOL_PATH -c '!analyze -v; q'
```

All five predate the 01-Sep DIMM change. The 02-Sep storm is the first heavy load since, and it is the same class of fault.

## Memtest results — 2026-09-04

Memtest86+ v8.10, PAR 8T, 668MHz (DDR3-1337) CAS 11-11-11-30, **DRAM 1.50V / VCCIO auto** (stock, not the 1.55V/1.10V tune). Screenshots in `HW_TEST\`.

| Config | Time | Passes | Errors |
|---|---|---|---|
| 1 stick, Slot 1, 7.96GB (run A) | 3:32:29 | 4 | 0 |
| 1 stick, Slot 1, 7.96GB (run B) | 3:48:48 | 4 | 0 |
| 2 sticks, Slot 1+3, 15.9GB | 3:59:42 | 4 | 0 |
| 4 sticks, 31.9GB | 4:43:23 | 2 | **37454** |

The 32GB run is one continuous run photographed six times (test 6 frozen at 19487, test 9 climbing 624 -> 14561). Errors scattered 1.96GB-31.2GB, bit masks `00ff00ff`/`ffff00ff`, 1-8 bits, max contiguous 1 — signal integrity across 2 DIMMs per channel, not a bad cell.

**Both sticks are good. The 16GB pair is good, and good at stock voltage — the tuned voltages were never needed.** The RAM hypothesis for the 02-Sep storm is dead.

**Prime suspect is now the GPU.** `dcomp.dll` is DirectComposition and lives on the NVIDIA Quadro P2000 (driver 32.0.15.8216, Dec 2025). No TDR events rules out a driver hang, not corrupted composition state or bad VRAM. Current config: 2x8GB in A1+B1, DRAM 1.50V, VCCIO auto.

## Storage — secondary but real

- 20-Aug and 21-Aug: NTFS event 55, `Severity=Critical`, volume F:. The 21-Aug chkdsk scan said "Windows has found problems that must be fixed offline". The 29-Aug rescan was clean and F: is not dirty now.
- F: = Disk 2 = SSDPR-CX400-256-G2 (GOODRAM, DRAM-less, 5694 power-on hours). It hosts the RAG store including a 1.19 GB `vdb_relationships.json` rewritten every ingest. `disk` 153 IO retries: 3x on 29-Aug, 2x on 02-Sep.
- 27-Aug: `disk` 51 paging error on Harddisk1 = C: (Kingston SKC600).
- 29-Aug: `storahci` 129 x2, "Reset to device \Device\RaidPort1" — SATA controller stall.
- Intel Chipset SATA RAID driver 15.44.0.1015, dated 2018.
- SMART clean on all four SSDs: 0 read errors, 0 write errors, 32 C.

## Open actions

1. DONE 2026-09-04 — memtest at stock cleared both sticks and the 16GB pair; only 4 DIMMs fail.
2. DONE 2026-09-04 — WER local dumps armed for dwm.exe: `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\dwm.exe`, DumpFolder `C:\Dumps\dwm`, DumpType 2 (full), DumpCount 3. Next storm produces a real dump; read it with cdb.
3. VRAM stress test on the Quadro P2000 (OCCT video memory, 30-60 min) while the box is otherwise idle.
4. Move the RAG store off the CX400 (F:) to the Samsung 980 (X:).
5. Next ingest is now also the GPU experiment — if the storm returns, `C:\Dumps\dwm\*.dmp` is the evidence.

## RAG store state at time of writing

52 docs: 51 `processed`, 1 stuck at `handling` (`Technische Mechanik 1 Theorie-027-051.pdf`, 7 chunks). Graph 33405 nodes / 139068 edges. Zero NUL bytes in all store files. Still missing from the graph and present in IN\: `Kapitel12_Verzerrungszustand.pdf`, `Technische Mechanik 2 Theorie-7.pdf`, `Technische Mechanik 3 Theorie--3.pdf`. `lightrag\LOG\ingest_run.log` has no EXITCODE line — the run is void, do not delete the log.
