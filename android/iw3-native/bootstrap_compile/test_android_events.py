"""Host regression for the Android IW3 event adapter (not gameplay)."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent

class EventTests(unittest.TestCase):
    def test_auto_manual_reset(self):
        source = r"""
#include <cassert>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <thread>
void Sys_CreateEvent(bool,bool,void**);
void Sys_SetEvent(void**);
void Sys_ResetEvent(void**);
bool Sys_WaitForSingleObjectTimeout(void**,std::uint32_t);
void Sys_WaitForSingleObject(void**);
int main() {
    void* automatic=nullptr;
    Sys_CreateEvent(false,false,&automatic);
    assert(automatic);
    // Invalid handles must be safe and must never appear signaled.
    void* absent=nullptr;
    assert(!Sys_WaitForSingleObjectTimeout(nullptr,0));
    assert(!Sys_WaitForSingleObjectTimeout(&absent,0));
    Sys_SetEvent(nullptr);
    Sys_ResetEvent(nullptr);
    Sys_WaitForSingleObject(nullptr);
    Sys_SetEvent(&absent);
    Sys_ResetEvent(&absent);
    Sys_WaitForSingleObject(&absent);
    // Initially signaled auto-reset handles permit exactly one immediate wait.
    void* initial_auto=nullptr;
    Sys_CreateEvent(false,true,&initial_auto);
    assert(initial_auto);
    assert(Sys_WaitForSingleObjectTimeout(&initial_auto,0));
    assert(!Sys_WaitForSingleObjectTimeout(&initial_auto,0));
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    // A finite unsignaled wait must time out, not accidentally act like INFINITE.
    auto timeout_start=std::chrono::steady_clock::now();
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,25));
    auto timeout_elapsed=std::chrono::steady_clock::now()-timeout_start;
    assert(timeout_elapsed>=std::chrono::milliseconds(15));
    assert(timeout_elapsed<std::chrono::seconds(2));
    // Win32 auto-reset events are binary, not counting semaphores:
    // repeated SetEvent calls before a wait coalesce into one wakeup.
    Sys_SetEvent(&automatic);
    Sys_SetEvent(&automatic);
    assert(Sys_WaitForSingleObjectTimeout(&automatic,0));
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    Sys_SetEvent(&automatic);
    assert(Sys_WaitForSingleObjectTimeout(&automatic,0));
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    // Win32 INFINITE must wait for a future signal, then auto-consume it.
    std::atomic<bool> infinite_started{false};
    std::atomic<bool> infinite_finished{false};
    std::thread infinite_waiter([&]{
        infinite_started = true;
        infinite_finished = Sys_WaitForSingleObjectTimeout(&automatic,UINT32_MAX);
    });
    auto infinite_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1);
    while (!infinite_started && std::chrono::steady_clock::now()<infinite_deadline)
        std::this_thread::yield();
    assert(infinite_started);
    Sys_SetEvent(&automatic);
    infinite_waiter.join();
    assert(infinite_finished);
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    std::atomic<int> done{0};
    std::atomic<int> ready{0};
    std::thread a([&]{++ready; if (Sys_WaitForSingleObjectTimeout(&automatic,2000)) ++done;});
    std::thread b([&]{++ready; if (Sys_WaitForSingleObjectTimeout(&automatic,2000)) ++done;});
    auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1);
    while (ready.load()!=2 && std::chrono::steady_clock::now()<deadline)
        std::this_thread::yield();
    assert(ready==2);
    Sys_SetEvent(&automatic);
    while (done.load()!=1 && std::chrono::steady_clock::now()<deadline)
        std::this_thread::yield();
    assert(done==1);
    Sys_SetEvent(&automatic);
    a.join(); b.join();
    // Both waiters must have consumed exactly one signal; a timeout is failure.
    assert(done==2);
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    void* manual=nullptr;
    Sys_CreateEvent(true,true,&manual);
    assert(Sys_WaitForSingleObjectTimeout(&manual,0));
    assert(Sys_WaitForSingleObjectTimeout(&manual,0));
    Sys_ResetEvent(&manual);
    assert(!Sys_WaitForSingleObjectTimeout(&manual,0));
    Sys_SetEvent(&manual);
    assert(Sys_WaitForSingleObjectTimeout(&manual,0));
    // Manual-reset must release every waiter and stay signaled until reset.
    Sys_ResetEvent(&manual);
    std::atomic<int> manual_ready{0};
    std::atomic<int> manual_done{0};
    std::thread m1([&]{++manual_ready; if (Sys_WaitForSingleObjectTimeout(&manual,2000)) ++manual_done;});
    std::thread m2([&]{++manual_ready; if (Sys_WaitForSingleObjectTimeout(&manual,2000)) ++manual_done;});
    auto manual_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1);
    while (manual_ready.load()!=2 && std::chrono::steady_clock::now()<manual_deadline)
        std::this_thread::yield();
    assert(manual_ready==2);
    Sys_SetEvent(&manual);
    m1.join(); m2.join();
    assert(manual_done==2);
    assert(Sys_WaitForSingleObjectTimeout(&manual,0));
    Sys_ResetEvent(&manual);
    assert(!Sys_WaitForSingleObjectTimeout(&manual,0));
}
"""
        with tempfile.TemporaryDirectory() as temp:
            cpp = pathlib.Path(temp) / "test.cpp"
            exe = pathlib.Path(temp) / "test"
            cpp.write_text(source)
            subprocess.run(["g++", "-std=c++20", "-Wall", "-Wextra", "-Werror",
                            "-pthread", str(ROOT / "iw3_android_events.cpp"),
                            str(cpp), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True, timeout=10)

if __name__ == "__main__":
    unittest.main()
