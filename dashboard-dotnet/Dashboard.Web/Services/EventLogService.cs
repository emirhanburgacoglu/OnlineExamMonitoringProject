using Dashboard.Web.Data;
using Microsoft.EntityFrameworkCore;

namespace Dashboard.Web.Services;

public class EventLogService
{
    private readonly IDbContextFactory<AppDbContext> _dbFactory;

    public EventLogService(IDbContextFactory<AppDbContext> dbFactory)
    {
        _dbFactory = dbFactory;
    }

    public async Task<List<EventLog>> GetLastAsync(int studentId, int examId, int take = 10)
    {
        await using var db = await _dbFactory.CreateDbContextAsync();
        return await db.EventLogs
            .Where(x => x.StudentId == studentId && x.ExamId == examId)
            .OrderByDescending(x => x.Timestamp)
            .Take(take)
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task LogIfNewAsync(int studentId, int examId, SuspiciousEvent ev)
    {
        if (ev is null || ev.SuspicionScore <= 0.5) return;

        var eventAtUtc = ToUtc(ev.Timestamp);

        await using var db = await _dbFactory.CreateDbContextAsync();

        // Aynı olay +/-1sn içinde zaten varsa tekrar yazma
        var exists = await db.EventLogs.AnyAsync(x =>
            x.StudentId == studentId &&
            x.ExamId == examId &&
            x.EventType == ev.Event &&
            x.Timestamp >= eventAtUtc.AddSeconds(-1) &&
            x.Timestamp <= eventAtUtc.AddSeconds(1));

        if (exists) return;

        db.EventLogs.Add(new EventLog
        {
            StudentId = studentId,
            ExamId = examId,
            EventType = ev.Event,
            SuspicionScore = ev.SuspicionScore,
            Timestamp = eventAtUtc
        });

        try
        {
            await db.SaveChangesAsync();
        }
        catch (DbUpdateException)
        {
            // Yarış durumunda nadiren tekrara düşerse: yoksay
        }
    }

    private static DateTime ToUtc(double ts)
    {
        // Saniye mi, milisaniye mi?
        if (ts > 1e12)
            return DateTimeOffset.FromUnixTimeMilliseconds((long)ts).UtcDateTime;

        return DateTimeOffset.FromUnixTimeSeconds((long)Math.Round(ts)).UtcDateTime;
    }
}