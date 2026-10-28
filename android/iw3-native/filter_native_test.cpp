#include "q_shared.h"

#include <cassert>
#include <string>

int main()
{
    assert(Com_FilterPath("maps/*.bsp", "maps/mp_test.bsp", 0));
    assert(Com_FilterPath("maps\\*.bsp", "maps/mp_test.bsp", 0));
    assert(Com_FilterPath("maps:*.bsp", "maps\\mp_test.bsp", 0));
    assert(Com_FilterPath("MAPS/*.BSP", "maps/mp_test.bsp", 0));
    assert(!Com_FilterPath("MAPS/*.BSP", "maps/mp_test.bsp", 1));
    assert(Com_FilterPath("maps/mp_?.bsp", "maps/mp_a.bsp", 0));
    assert(!Com_FilterPath("maps/mp_?.bsp", "maps/mp_ab.bsp", 0));
    assert(Com_FilterPath("maps/[a-c]est.bsp", "maps/best.bsp", 0));
    assert(!Com_FilterPath("maps/[a-c]est.bsp", "maps/zest.bsp", 0));
    assert(Com_FilterPath("[[a-c]]", "b", 0));
    assert(!Com_FilterPath("maps/[abc", "maps/a", 0));
    assert(!Com_FilterPath(nullptr, "maps/a.bsp", 0));
    assert(!Com_FilterPath("maps/*.bsp", nullptr, 0));

    std::string longLiteral(MAX_TOKEN_CHARS + 8, 'a');
    std::string longFilter = "*" + longLiteral;
    std::string longName = "x" + longLiteral;
    assert(!Com_Filter(longFilter.c_str(), longName.data(), 1));

    // The original path helper truncates to MAX_QPATH-1 before matching.
    std::string prefix(MAX_QPATH - 1, 'x');
    std::string longer = prefix + "different-tail";
    assert(Com_FilterPath(prefix.c_str(), longer.c_str(), 1));
    return 0;
}
