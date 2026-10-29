// whisper-cli.exe —— whisper.cpp 命令行兼容层
// 本机没有 whisper.cpp，上游 scripts/assemble.py / scripts/align.py 都要调 whisper-cli。
// 这里用本机 FunASR 做同样的事，并输出 whisper.cpp 的 JSON 格式。
// 用法：whisper-cli -m <model> -l <lang> [--prompt "..."] [-ml 1] -oj -of <prefix> -f <wav>
using System;
using System.Diagnostics;
using System.Text;

class WhisperCliShim
{
    static int Main(string[] args)
    {
        string py = Environment.GetEnvironmentVariable("DHK_ASR_PYTHON");
        if (string.IsNullOrEmpty(py)) py = @"E:\AI\envs\voxcpm\Scripts\python.exe";
        string script = Environment.GetEnvironmentVariable("DHK_ASR_SCRIPT");
        if (string.IsNullOrEmpty(script)) script = @"E:\dsh-agents\skills\digital-human-koubo\scripts\local\asr_funasr.py";

        StringBuilder sb = new StringBuilder();
        sb.Append('"'); sb.Append(script); sb.Append('"');
        foreach (string a in args)
        {
            sb.Append(' ');
            sb.Append('"');
            sb.Append(a.Replace("\"", "\\\""));
            sb.Append('"');
        }

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = py;
        psi.Arguments = sb.ToString();
        psi.UseShellExecute = false;
        psi.RedirectStandardOutput = false;
        psi.RedirectStandardError = false;
        psi.CreateNoWindow = true;
        psi.WorkingDirectory = Environment.CurrentDirectory;

        Process p = Process.Start(psi);
        p.WaitForExit();
        return p.ExitCode;
    }
}
