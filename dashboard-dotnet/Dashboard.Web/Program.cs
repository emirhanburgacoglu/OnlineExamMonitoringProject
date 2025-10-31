using Dashboard.Web.Components;
using Dashboard.Web.Services;
using Dashboard.Web.Data;                // <-- DbContext için
using Microsoft.AspNetCore.Components.Web;
using Microsoft.EntityFrameworkCore;     // <-- UseSqlite için
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

// 1) Razor Components + Interactive Server
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// 2) EF Core (SQLite) - Blazor Server için DbContextFactory önerilir
builder.Services.AddDbContextFactory<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")
                      ?? "Data Source=project.db"));

// 3) Python API'ye konuşacak Typed HttpClient
builder.Services.AddHttpClient<PythonApiService>(client =>
{
    client.BaseAddress = new Uri("http://127.0.0.1:8000");
    client.Timeout = TimeSpan.FromSeconds(5);
})
.ConfigurePrimaryHttpMessageHandler(() =>
{
    return new HttpClientHandler
    {
        ServerCertificateCustomValidationCallback = (sender, cert, chain, sslPolicyErrors) => true
    };
});

// 4) Uygulama servisleri
builder.Services.AddScoped<EventLogService>(); // <-- DB log servisi
builder.Services.AddMudServices();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

// app.UseHttpsRedirection(); // Python HTTP olduğu için kapalı
app.UseStaticFiles();
app.UseAntiforgery();

// 5) Interaktif server render mode'u etkinleştir
app.MapRazorComponents<App>()
   .AddInteractiveServerRenderMode();

// 6) Opsiyonel: Migration uygula + basit seed (Varsayılan öğrenci/sınav oluşturur)
using (var scope = app.Services.CreateScope())
{
    var dbFactory = scope.ServiceProvider.GetRequiredService<IDbContextFactory<AppDbContext>>();
    await using var db = await dbFactory.CreateDbContextAsync();
    db.Database.Migrate();

    if (!db.Students.Any())
    {
        db.Students.Add(new Student
        {
            Name = "Varsayılan Öğrenci",
            StudentNumber = "0001"
        });
        await db.SaveChangesAsync();
    }

    if (!db.Exams.Any())
    {
        db.Exams.Add(new Exam
        {
            CourseName = "Varsayılan Sınav",
            StartTime = DateTime.UtcNow
        });
        await db.SaveChangesAsync();
    }
}

app.Run();