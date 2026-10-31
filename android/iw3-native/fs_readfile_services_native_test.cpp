#include "qcommon/qcommon.h"
#include "qcommon/fast_critical_section.h"

#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <thread>
#include <vector>

extern int logfile;

static void test_original_logfile_open_reads_engine_state() {
    logfile = 0;
    assert(!Com_LogFileOpen());
    logfile = 1;
    assert(Com_LogFileOpen());
    logfile = 0;
    assert(!Com_LogFileOpen());
}

static void test_writer_waits_while_reader_count_is_nonzero() {
    FastCriticalSection section{};
    __atomic_store_n(&section.readCount, 1U, __ATOMIC_SEQ_CST);
    std::atomic<bool> acquired{false};
    std::thread waiter([&] {
        Sys_LockWrite(&section);
        acquired.store(true, std::memory_order_release);
        Sys_UnlockWrite(&section);
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(15));
    assert(!acquired.load(std::memory_order_acquire));
    assert(__atomic_load_n(&section.writeCount, __ATOMIC_SEQ_CST) == 0U);
    __atomic_store_n(&section.readCount, 0U, __ATOMIC_SEQ_CST);
    waiter.join();
    assert(acquired.load(std::memory_order_acquire));
    assert(__atomic_load_n(&section.writeCount, __ATOMIC_SEQ_CST) == 0U);
}

static void test_writer_exclusion_under_contention() {
    FastCriticalSection section{};
    constexpr int kThreadCount = 8;
    constexpr int kIterations = 12000;
    std::atomic<int> ready{0};
    std::atomic<bool> start{false};
    uint64_t protectedCounter = 0;
    std::vector<std::thread> workers;
    workers.reserve(kThreadCount);
    for (int i = 0; i < kThreadCount; ++i) {
        workers.emplace_back([&] {
            ready.fetch_add(1, std::memory_order_release);
            while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
            for (int n = 0; n < kIterations; ++n) {
                Sys_LockWrite(&section);
                ++protectedCounter;
                Sys_UnlockWrite(&section);
            }
        });
    }
    while (ready.load(std::memory_order_acquire) != kThreadCount) std::this_thread::yield();
    start.store(true, std::memory_order_release);
    for (auto &worker : workers) worker.join();
    assert(protectedCounter == static_cast<uint64_t>(kThreadCount) * kIterations);
    assert(__atomic_load_n(&section.writeCount, __ATOMIC_SEQ_CST) == 0U);
}

int main() {
    test_original_logfile_open_reads_engine_state();
    test_writer_waits_while_reader_count_is_nonzero();
    test_writer_exclusion_under_contention();
    return 0;
}
