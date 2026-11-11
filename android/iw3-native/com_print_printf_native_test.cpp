extern void Com_Printf(int channel, const char *fmt, ...);

int main()
{
    Com_Printf(5, "IW3_PRINTF_PROBE_%d\n", 7);
    return 0;
}
