package com.llmytranslate.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.llmytranslate.android.utils.PerformanceData

/**
 * PerformanceMonitorCard displays real-time performance metrics and timing data.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PerformanceMonitorCard(
    performanceData: PerformanceData,
    modifier: Modifier = Modifier,
    expanded: Boolean = false,
    onExpandToggle: () -> Unit = {}
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        onClick = onExpandToggle
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Speed,
                        contentDescription = "Performance",
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Performance Monitor",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                
                // Quick stats
                PerformanceQuickStats(performanceData)
            }
            
            if (expanded) {
                Spacer(modifier = Modifier.height(16.dp))
                PerformanceDetailView(performanceData)
            }
        }
    }
}

@Composable
private fun PerformanceQuickStats(performanceData: PerformanceData) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Total operations
        QuickStatChip(
            icon = Icons.Default.Timer,
            label = "Ops",
            value = performanceData.getTotalOperations().toString(),
            color = MaterialTheme.colorScheme.primary
        )
        
        // Slowest operation
        performanceData.getSlowestOperation()?.let { (operation, time) ->
            QuickStatChip(
                icon = Icons.Default.Speed,
                label = "Slow",
                value = "${time}ms",
                color = if (time > 1000) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary
            )
        }
    }
}

@Composable
private fun QuickStatChip(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
    color: Color
) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = color.copy(alpha = 0.1f),
        modifier = Modifier.padding(2.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                modifier = Modifier.size(14.dp),
                tint = color
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.labelSmall,
                color = color,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun PerformanceDetailView(performanceData: PerformanceData) {
    Column {
        Text(
            text = "Detailed Timing",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        LazyColumn(
            modifier = Modifier.heightIn(max = 300.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            items(performanceData.stageTimes.toList().sortedByDescending { it.second }) { (operation, time) ->
                PerformanceOperationRow(
                    operation = operation,
                    time = time,
                    count = performanceData.operationCounts[operation] ?: 1,
                    avgTime = performanceData.getAverageTime(operation)
                )
            }
        }
    }
}

@Composable
private fun PerformanceOperationRow(
    operation: String,
    time: Long,
    count: Int,
    avgTime: Long
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f),
                shape = RoundedCornerShape(8.dp)
            )
            .padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = operation.replace("_", " ").lowercase().split(" ").joinToString(" ") { 
                    it.replaceFirstChar { char -> char.uppercase() }
                },
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium
            )
            
            if (count > 1) {
                Text(
                    text = "$count operations",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            }
        }
        
        Column(
            horizontalAlignment = Alignment.End
        ) {
            Text(
                text = "${time}ms",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = getTimeColor(time)
            )
            
            if (count > 1) {
                Text(
                    text = "avg: ${avgTime}ms",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            }
        }
    }
}

@Composable
private fun getTimeColor(time: Long): Color {
    return when {
        time < 100 -> Color(0xFF4CAF50) // Green for fast operations
        time < 500 -> Color(0xFFFF9800) // Orange for medium operations
        time < 1000 -> Color(0xFFFF5722) // Red-orange for slow operations
        else -> Color(0xFFF44336) // Red for very slow operations
    }
}

/**
 * Compact performance indicator for showing in app bars or status areas.
 */
@Composable
fun PerformanceIndicator(
    performanceData: PerformanceData,
    modifier: Modifier = Modifier
) {
    val slowestOperation = performanceData.getSlowestOperation()
    val totalOps = performanceData.getTotalOperations()
    
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.6f)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.Speed,
                contentDescription = "Performance",
                modifier = Modifier.size(16.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Spacer(modifier = Modifier.width(4.dp))
            
            Text(
                text = "$totalOps ops",
                style = MaterialTheme.typography.labelSmall,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.primary
            )
            
            slowestOperation?.let { (_, time) ->
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "↑${time}ms",
                    style = MaterialTheme.typography.labelSmall,
                    fontFamily = FontFamily.Monospace,
                    color = getTimeColor(time),
                    fontSize = 10.sp
                )
            }
        }
    }
}
