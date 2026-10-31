extern void Com_PrintWarning(int channel, const char *fmt, ...);

int main()
{
    Com_PrintWarning(5, "IW3_WARNING_PROBE_%d\n", 7);
    return 0;
}
