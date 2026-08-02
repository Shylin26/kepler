# Lesson 2: Processes (Part 3 — Threads)

**Date:** 2 August 2026
**Status:** in progress

## What problem do threads solve that processes alone don't?
A process gives full isolation, but that isolation is expensive — creating a new process per client (like spawning one for every web server connection) means paying full memory-space setup and expensive context switches every time. Threads solve this by sharing the same address space as the rest of the process, so multiple things can run concurrently within one program without that isolation cost — at the price of no longer having memory protection between them.

## What is a thread, in one sentence?
A thread is a separate flow of execution within a process that shares the process's memory (heap, globals, open files) but keeps its own private stack and register state.

## Why is switching between threads of the same process cheaper than switching between processes?
- Register state (PC, stack pointer, general registers) still gets saved/loaded on every thread switch, same as a process switch — that part doesn't go away.
- Threads of the same process share the same address space, so TLB entries stay valid across the switch — no TLB flush needed, unlike switching processes.
- Because threads of the same process touch overlapping memory (shared heap, shared globals), there's a real chance cache contents from one thread are still useful to the next — unlike switching to a totally unrelated process, where the cache is cold.

## What is a race condition, and why does it happen even for something as simple as `counter = counter + 1`?
`counter = counter + 1` isn't one atomic step — it's three: read counter into a register, add 1, write the register back to memory. If Thread A reads counter (5) and gets switched out before writing back, Thread B can read that same stale 5, and both threads eventually write back 6 — even though two increments happened, one gets silently lost. Counter should be 7, ends up 6, with no error or crash — just a quietly wrong number.

## What is a lock / mutex, and what does it actually guarantee?
A lock guarantees that only one thread at a time can be inside a critical section — the specific read-modify-write region, like the counter update. A thread must acquire the lock before entering, and other threads attempting to acquire it block until it's released. This doesn't block all memory access — only entry into that specific guarded region.

## Open questions / things I'm still fuzzy on
Still fuzzy on what happens if a thread crashes or gets stuck while holding a lock — does every other thread waiting on it just hang forever?
