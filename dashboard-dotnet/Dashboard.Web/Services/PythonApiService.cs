using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace Dashboard.Web.Services;

public class SuspiciousEvent
{
    [JsonPropertyName("timestamp")] public double Timestamp { get; set; }
    [JsonPropertyName("event")] public string Event { get; set; } = "Yükleniyor...";
    [JsonPropertyName("suspicion_score")] public double SuspicionScore { get; set; }
}

public class SnapshotResponse
{
    [JsonPropertyName("image_url")] public string? ImageUrl { get; set; }
}

public class PythonApiService
{
    private readonly HttpClient _httpClient;
    public PythonApiService(HttpClient httpClient) { _httpClient = httpClient; }

    public async Task<SuspiciousEvent?> GetLatestEventAsync()
    {
        try { return await _httpClient.GetFromJsonAsync<SuspiciousEvent>("/latest_event"); }
        catch (Exception ex) { Console.WriteLine($"API Hatası: {ex.Message}"); return null; }
    }

    public async Task<string?> GetSnapshotAsync()
    {
        try
        {
            var res = await _httpClient.GetFromJsonAsync<SnapshotResponse>("/snapshot");
            return res?.ImageUrl;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Snapshot Hatası: {ex.Message}");
            return null;
        }
    }
}