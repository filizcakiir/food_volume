import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:food_calorie_app/generated/app_localizations.dart';
import '../../config/theme.dart';
import '../../services/stats_service.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  final StatsService _statsService = StatsService();
  String _selectedPeriod = 'week';
  bool _isLoading = true;

  // Backend data
  Map<String, dynamic>? _dailyData;
  List<dynamic>? _weeklyData;
  Map<String, dynamic>? _mealDistribution;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Load all data in parallel
      final results = await Future.wait([
        _statsService.getDailyLog(),
        _statsService.getWeeklyLog(),
        _statsService.getMealDistribution(),
      ]);

      if (mounted) {
        setState(() {
          if (results[0]['success'] == true) {
            _dailyData = results[0]['data'];
          }
          if (results[1]['success'] == true) {
            _weeklyData = results[1]['data'];
          }
          if (results[2]['success'] == true) {
            _mealDistribution = results[2]['data'];
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.stats),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPeriodSelector(),
                  const SizedBox(height: 24),
                  _buildTodaySummary(),
                  const SizedBox(height: 24),
                  _buildCaloriesChart(),
                  const SizedBox(height: 24),
                  _buildMacrosChart(),
                  const SizedBox(height: 24),
                  _buildMealDistribution(),
                ],
              ),
            ),
    );
  }

  Widget _buildPeriodSelector() {
    final l10n = AppLocalizations.of(context)!;
    final periods = {
      'week': l10n.week,
      'month': l10n.month,
      'year': l10n.year,
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Row(
          children: periods.entries.map((entry) {
            final isSelected = _selectedPeriod == entry.key;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4.0),
                child: ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _selectedPeriod = entry.key;
                    });
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isSelected
                        ? AppTheme.primaryColor
                        : Colors.grey.shade200,
                    foregroundColor:
                        isSelected ? Colors.white : AppTheme.textPrimaryColor,
                    elevation: isSelected ? 2 : 0,
                  ),
                  child: Text(entry.value),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildTodaySummary() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final calories = ((_dailyData?['total_calories'] ?? 0) as num).toInt();
    final protein = ((_dailyData?['protein'] ?? 0) as num).toInt();
    final carbs = ((_dailyData?['carbs'] ?? 0) as num).toInt();
    final fat = ((_dailyData?['fat'] ?? 0) as num).toInt();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.todaySummary,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildSummaryItem(l10n.calories, calories.toString(), l10n.kcal, AppTheme.accentColor),
                _buildSummaryItem(l10n.protein, protein.toString(), l10n.grams, Colors.blue),
                _buildSummaryItem(l10n.carbs, carbs.toString(), l10n.grams, Colors.orange),
                _buildSummaryItem(l10n.fat, fat.toString(), l10n.grams, Colors.amber),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, String unit, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          unit,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            color: AppTheme.textSecondaryColor,
          ),
        ),
      ],
    );
  }

  Widget _buildCaloriesChart() {
    final l10n = AppLocalizations.of(context)!;

    // Convert weekly data to chart spots
    List<FlSpot> spots = [];
    if (_weeklyData != null && _weeklyData!.isNotEmpty) {
      for (int i = 0; i < _weeklyData!.length && i < 7; i++) {
        final calories = ((_weeklyData![i]['total_calories'] ?? 0) as num).toDouble();
        spots.add(FlSpot(i.toDouble(), calories));
      }
    } else {
      // If no data, show empty chart
      for (int i = 0; i < 7; i++) {
        spots.add(FlSpot(i.toDouble(), 0));
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.caloriesThisWeek,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 24),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(show: false),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final days = [l10n.mon, l10n.tue, l10n.wed, l10n.thu, l10n.fri, l10n.sat, l10n.sun];
                          if (value.toInt() >= 0 && value.toInt() < days.length) {
                            return Text(days[value.toInt()]);
                          }
                          return const Text('');
                        },
                      ),
                    ),
                    topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: AppTheme.primaryColor,
                      barWidth: 3,
                      dotData: FlDotData(show: true),
                      belowBarData: BarAreaData(
                        show: true,
                        color: AppTheme.primaryColor.withOpacity(0.1),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMacrosChart() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final protein = ((_dailyData?['protein'] ?? 0) as num).toDouble();
    final carbs = ((_dailyData?['carbs'] ?? 0) as num).toDouble();
    final fat = ((_dailyData?['fat'] ?? 0) as num).toDouble();

    // Calculate calories from macros (protein/carbs = 4 cal/g, fat = 9 cal/g)
    final proteinCals = protein * 4;
    final carbsCals = carbs * 4;
    final fatCals = fat * 9;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.macronutrientsToday,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 24),
            SizedBox(
              height: 200,
              child: PieChart(
                PieChartData(
                  sectionsSpace: 2,
                  centerSpaceRadius: 60,
                  sections: [
                    PieChartSectionData(
                      value: proteinCals,
                      title: '${l10n.protein}\n${protein.toInt()}g',
                      color: Colors.blue,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: carbsCals,
                      title: '${l10n.carbs}\n${carbs.toInt()}g',
                      color: Colors.orange,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: fatCals,
                      title: '${l10n.fat}\n${fat.toInt()}g',
                      color: Colors.amber,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMealDistribution() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final distribution = _mealDistribution?['distribution'] as Map<String, dynamic>?;
    final breakfastCals = ((distribution?['breakfast']?['total_calories'] ?? 0) as num).toDouble();
    final lunchCals = ((distribution?['lunch']?['total_calories'] ?? 0) as num).toDouble();
    final dinnerCals = ((distribution?['dinner']?['total_calories'] ?? 0) as num).toDouble();
    final snackCals = ((distribution?['snack']?['total_calories'] ?? 0) as num).toDouble();
    final totalCals = ((_dailyData?['total_calories'] ?? 2000) as num).toDouble();
    final maxCalories = totalCals > 0 ? totalCals : 2000.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.mealDistribution,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 16),
            _buildMealBar(l10n.breakfast, breakfastCals, maxCalories, Colors.orange),
            const SizedBox(height: 12),
            _buildMealBar(l10n.lunch, lunchCals, maxCalories, AppTheme.secondaryColor),
            const SizedBox(height: 12),
            _buildMealBar(l10n.dinner, dinnerCals, maxCalories, AppTheme.primaryColor),
            const SizedBox(height: 12),
            _buildMealBar(l10n.snack, snackCals, maxCalories, Colors.purple),
          ],
        ),
      ),
    );
  }

  Widget _buildMealBar(String label, double calories, double maxCalories, Color color) {
    final l10n = AppLocalizations.of(context)!;
    final percentage = (calories / maxCalories).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '${calories.toStringAsFixed(0)} ${l10n.kcal}',
              style: TextStyle(color: color, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: percentage,
          backgroundColor: Colors.grey.shade200,
          color: color,
          minHeight: 8,
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }
}
