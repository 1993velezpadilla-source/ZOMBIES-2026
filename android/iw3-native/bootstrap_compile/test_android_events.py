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
    assert(!Sys_WaitForSingleObjectTimeout(&automatic,0));
    Sys_SetEvent(&automatic);
    assert(Sys_WaitForSingleObjectTimeout(&automatic,0));
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
